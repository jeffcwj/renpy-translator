import io
import os
import re
import threading
import time
import traceback

import httpx
import openai
from openai import OpenAI
import json
import concurrent.futures
from openai.types import Model, ModelDeleted

from my_log import log_print
from string_tool import remove_upprintable_chars, split_strings

# "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"
limit_time_span_dic = dict()
openai_template_file = 'openai_template.json'

# 模板缓存，避免每次 API 调用都读文件
_template_cache = None
_template_mtime = 0


def _load_template_cached():
    """读取并缓存 openai_template.json，文件修改后自动刷新"""
    global _template_cache, _template_mtime
    if not os.path.isfile(openai_template_file):
        return None
    mtime = os.path.getmtime(openai_template_file)
    if _template_cache is not None and mtime == _template_mtime:
        return _template_cache
    try:
        f = io.open(openai_template_file, 'r', encoding='utf-8')
        raw = f.read()
        f.close()
        _template_cache = raw
        _template_mtime = mtime
        return raw
    except Exception:
        msg = traceback.format_exc()
        log_print(msg)
        return None


def _try_fix_truncated_json(text):
    """尝试修复被截断的 JSON 字典，返回修复后的字符串或 None"""
    if text is None:
        return None
    text = text.strip()
    # 已经是合法 JSON 就直接返回
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    # 如果不是以 { 开头，无法修复
    if not text.startswith('{'):
        return None
    # 策略1: 去掉末尾不完整的 key-value 对，补上 }
    # 找最后一个完整的 "key": "value" 对的结束位置
    # 匹配模式: "数字": "内容"  后面跟 , 或 }
    last_complete = -1
    # 找所有完整的 value 结束位置（引号后跟逗号或空白）
    for m in re.finditer(r'"[^"]*"\s*:\s*"(?:[^"\\]|\\.)*"', text):
        last_complete = m.end()
    if last_complete > 0:
        fixed = text[:last_complete].rstrip().rstrip(',') + '}'
        try:
            json.loads(fixed)
            return fixed
        except Exception:
            pass
    # 策略2: 已禁用——直接在截断处补 "} 可能闭合不完整的 value，导致翻译内容错乱
    # 无法修复则放弃，走 spilt_half_and_re_translate 重试逻辑
    return None


class TranslateResponse:
    def __init__(self, ori, res):
        self.untranslatedText = ori
        self.translatedText = res


class OpenAITranslate(object):
    lock = threading.Lock()
    count = 0

    def __init__(self, app_key, rpm, rps, tpm, model, base_url, time_out, max_length, proxies=None):
        self.app_key = app_key
        self.rpm = int(rpm)
        self.rps = int(rps)
        self.tpm = int(tpm)
        self.model = model
        self.base_url = base_url
        self.proxies = proxies
        self.timeout = int(time_out)
        self.max_length = int(max_length)

    def reset(self, app_key, rpm, rps, tpm, model, base_url, time_out, max_length, proxies=None):
        self.app_key = app_key
        self.rpm = int(rpm)
        self.rps = int(rps)
        self.tpm = int(tpm)
        self.model = model
        self.base_url = base_url
        self.proxies = proxies
        self.timeout = int(time_out)
        self.max_length = int(max_length)

    def translate(self, q, source, target):
        result_arrays = split_strings(q, self.max_length)
        ret_l = []
        to_do = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for idx, result_array in enumerate(result_arrays):
                if len(result_array) == 0:
                    continue
                future = executor.submit(self.translate_limit, result_array, source, target)
                to_do.append(future)
        for future in to_do:
            result = future.result()
            if result is not None and 'l' in result.keys():
                ret_l = ret_l + result['l']
        limit_time_span_dic.clear()
        return ret_l

    def spilt_half_and_re_translate(self, data, source, target):
        half = int(len(data) / 2)
        data_1 = data[:half]
        data_2 = data[half:]
        dic1 = self.translate_limit(data_1, source, target)
        dic2 = self.translate_limit(data_2, source, target)
        dic = dict()
        l = []
        if dic1 is not None and 'l' in dic1.keys():
            l = dic1['l']
        if dic2 is not None and 'l' in dic2.keys():
            l = l + dic2['l']
        # 修复: 原来 len(l) < 0 永远不成立，改为 == 0
        if len(l) == 0:
            return None
        dic['l'] = l
        return dic

    def translate_limit(self, data, source, target):
        try:
            if self.base_url is not None and self.base_url != "" and len(self.base_url) > 0:
                client = OpenAI(
                    # This is the default and can be omitted
                    api_key=self.app_key,
                    base_url=self.base_url,
                    http_client=httpx.Client(
                        proxies=self.proxies,
                        transport=httpx.HTTPTransport(local_address="0.0.0.0"))
                )
            else:
                client = OpenAI(
                    # This is the default and can be omitted
                    api_key=self.app_key,
                    http_client=httpx.Client(
                        proxies=self.proxies,
                        transport=httpx.HTTPTransport(local_address="0.0.0.0"))
                )
            self.lock.acquire()
            t_minute = time.strftime("%H:%M")
            if t_minute not in limit_time_span_dic:
                limit_time_span_dic[t_minute] = 1
            else:
                limit_time_span_dic[t_minute] = limit_time_span_dic[t_minute] + 1
            # RPM (requests per minute)
            if limit_time_span_dic[t_minute] > self.rpm:
                log_print("RPM (requests per minute) exceed,start waiting 65 seconds")
                time.sleep(65)
                limit_time_span_dic.clear()
                self.count = 0

            t_second = int(time.time())
            if t_second not in limit_time_span_dic:
                limit_time_span_dic[t_second] = 1
            else:
                limit_time_span_dic[t_second] = limit_time_span_dic[t_second] + 1
            # RPS (requests per second)
            if limit_time_span_dic[t_second] >= self.rps:
                time.sleep(1)
            ori_dic = dict()
            for i, e in enumerate(data):
                ori_dic[i] = e
            js = json.dumps(ori_dic)
            self.count = self.count + len(js) * 1.5
            if self.count >= self.tpm:
                log_print("TOKEN LIMITS exceed. start waiting 70 seconds...")
                time.sleep(70)
                limit_time_span_dic.clear()
                self.count = 0
                self.lock.release()
                return self.translate_limit(data, source, target)
            self.lock.release()
            try:
                source_template = '#SOURCE_LANGUAGE_ID!@$^#'
                target_template = '#TARGET_LANGAUGE_ID!@$^#'
                js_template = '#JSON_DATA_WAITING_FOR_TRANSLATE_ID!@$^#'
                messages = []
                # 使用缓存读取模板
                raw_template = _load_template_cached()
                if raw_template:
                    template = raw_template.replace(source_template, source)
                    template = template.replace(target_template, target)
                    try:
                        messages = json.loads(template)
                    except:
                        pass
                if not messages:
                    log_print('{0} is not a valid json template, please check the template file!'.format(openai_template_file))
                    return None
                for message in messages:
                    for key, value in message.items():
                        if js_template in value:
                            message[key] = value.replace(js_template, js)

                if source is not None and source != 'AUTO':
                    pass
                else:
                    source = ''
                chat_completion = client.with_options(timeout=self.timeout, max_retries=2).chat.completions.create(
                    messages=messages,
                    model=self.model,
                    # response_format={"type": "json_object"},
                )
            except openai.APIConnectionError as e:
                log_print("The server could not be reached")
                log_print(e.__cause__)  # an underlying Exception, likely raised within httpx.
                log_print(e)
                log_print(data)
                return None
            except openai.RateLimitError as e:
                log_print("A 429 status code was received; we should back off a bit.")
                log_print(e)
                log_print(data)
                return None
            except openai.APIStatusError as e:
                log_print("Another non-200-range status code was received:{0} {1}".format(e.status_code, e.response))
                log_print(e)
                log_print(data)
                return None

            # 检查是否因为输出过长被截断
            finish_reason = None
            try:
                finish_reason = chat_completion.choices[0].finish_reason
            except Exception:
                pass
            if finish_reason == 'length':
                log_print('WARNING: AI output was truncated (finish_reason=length). Batch has {0} items, consider reducing max_length parameter.'.format(len(data)))

            raw_content = str(chat_completion.choices[0].message.content)
            # 剥离 AI 返回的 markdown 代码块标记（```json ... ```）
            raw_content = raw_content.strip()
            if raw_content.startswith('```'):
                first_newline = raw_content.find('\n')
                if first_newline != -1:
                    raw_content = raw_content[first_newline + 1:]
                if raw_content.endswith('```'):
                    raw_content = raw_content[:-3]
                raw_content = raw_content.strip()

            try:
                result = json.loads(raw_content)
                log_print('part translation success,still in progress,please waiting...')
            except Exception as e:
                # 尝试修复被截断的 JSON
                if finish_reason == 'length':
                    log_print('Attempting to fix truncated JSON response...')
                    fixed = _try_fix_truncated_json(raw_content)
                    if fixed is not None:
                        try:
                            result = json.loads(fixed)
                            log_print('Truncated JSON fixed successfully, recovered {0} items (original batch: {1})'.format(len(result), len(ori_dic)))
                        except Exception:
                            result = None
                    else:
                        result = None
                else:
                    result = None

                if result is None:
                    if len(data) < 5:
                        log_print('openai return an error json format')
                        log_print('Raw response: ' + raw_content[:500])
                        log_print('Lost {0} lines:'.format(len(data)))
                        for idx, text in enumerate(data):
                            log_print('  [{0}] {1}'.format(idx, text[:100]))
                        return None
                    else:
                        return self.spilt_half_and_re_translate(data, source, target)

            dic = dict()
            l = []
            if len(result) != len(ori_dic):
                # 如果是截断导致部分返回，尝试用已有的翻译结果（而不是全部丢弃）
                if finish_reason == 'length' and len(result) > 0:
                    log_print('Partial result: got {0}/{1} items due to truncation, using available translations'.format(len(result), len(ori_dic)))
                    # 收集已翻译的部分
                    translated_keys = set()
                    for i in result:
                        try:
                            num = int(remove_upprintable_chars(i))
                            if num in ori_dic:
                                translateResponse = TranslateResponse(ori_dic[num], result[i])
                                l.append(translateResponse)
                                translated_keys.add(num)
                        except Exception:
                            pass
                    # 对未翻译的部分递归翻译
                    untranslated_data = []
                    for k in ori_dic:
                        if k not in translated_keys:
                            untranslated_data.append(ori_dic[k])
                    if untranslated_data:
                        log_print('Re-translating {0} remaining untranslated lines...'.format(len(untranslated_data)))
                        retry_result = self.translate_limit(untranslated_data, source, target)
                        if retry_result is not None and 'l' in retry_result.keys():
                            l = l + retry_result['l']
                    dic['l'] = l
                    return dic
                elif len(data) < 5:
                    log_print('translated result can not match the untranslated contents')
                    log_print('Expected {0} items, got {1}'.format(len(ori_dic), len(result)))
                    log_print(result)
                    log_print(ori_dic)
                    return None
                else:
                    return self.spilt_half_and_re_translate(data, source, target)

            isCorrectId = True
            for i in result:
                try:
                    num = int(remove_upprintable_chars(i))
                except Exception as e:
                    isCorrectId = False
                    break
            if not isCorrectId:
                if len(data) < 5:
                    log_print('open ai return an error id')
                    log_print(result)
                    log_print(ori_dic)
                    return None
                else:
                    return self.spilt_half_and_re_translate(data, source, target)
            for i in result:
                num = int(remove_upprintable_chars(i))
                if num in ori_dic:
                    translateResponse = TranslateResponse(ori_dic[num], result[i])
                    l.append(translateResponse)
            dic['l'] = l
            return dic
        except Exception as e:
            msg = traceback.format_exc()
            log_print(msg)
            if os.path.isfile('translating'):
                os.remove('translating')
