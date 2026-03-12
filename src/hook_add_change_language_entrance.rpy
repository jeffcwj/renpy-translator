init python early hide:
    import os
    global importlib
    global inspect
    import importlib
    import inspect
    global check_function_exists
    def check_function_exists(module_name, function_name):
        try:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            if inspect.isfunction(function):
                return True
            else:
                return False
        except ImportError:
            return False
        except AttributeError:
            return False

    global my_old_show_screen
    my_old_show_screen = renpy.show_screen
    global my_old_lookup
    my_old_lookup = None
    if check_function_exists('renpy.ast.Translate','lookup'):
        my_old_lookup = renpy.ast.Translate.lookup
    def my_show_screen(_screen_name, *_args, **kwargs):
        if _screen_name == 'director':
            if my_old_lookup is not None:
                renpy.ast.Translate.lookup = my_old_lookup
        rv = my_old_show_screen(_screen_name, *_args, **kwargs)
        if _screen_name == 'preferences':
            try:
                my_old_show_screen('language_overlay')
            except Exception:
                pass
        return rv
    renpy.show_screen = my_show_screen

screen language_overlay():
    zorder 100
    if renpy.get_screen("preferences"):
        python:
            _tl_languages = sorted(
                l for l in renpy.known_languages() if l is not None
            )
        vbox:
            align(.99, .99)
            hbox:
                box_wrap True
                vbox:
                    label _("Language")
                    textbutton "Default" action Language(None)
                    for i in _tl_languages:
                        if i is not None and i != 'None':
                            textbutton "%s" % i action Language(i)
