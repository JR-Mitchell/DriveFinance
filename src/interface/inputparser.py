class BaseParser(object):
    """ Abstract class for object with functions safely callable at runtime

    :param offset:
    :type offset:
    """
    def __init__(self,offset):
        self._parser_offset = offset

    @staticmethod
    def _parseMethod(func_dict,*types):
        """ Decorator used to denote functions callable at runtime

        :param func_dict: the access dictionary that the function should be
            available from
        :type func_dict: dict
        """
        def decorator(function):
            def wrapped(self,*passed_args):
                if len(passed_args) != len(types) + self._parser_offset:
                    self._parser_handle_incorrect_argno(
                        function.__name__,
                        len(types),
                        passed_args[:self._parser_offset])
                new_args = list(passed_args[:self._parser_offset])
                for i,arg in enumerate(passed_args[self._parser_offset:]):
                    try:
                        new_args.append(types[i](arg))
                    except Exception as e:
                        self._parser_handle_conversion_error(
                            function.__name__, arg,
                            types[i], e)
                return self._parser_handle_func_result(function(
                    self,
                    *new_args))
            func_dict[function.__name__] = wrapped
            return function
        return decorator

    def _parser_handle_incorrect_argno(self,func_name,exp_len,passed):
        """ Virtual function for handling a runtime call with the wrong number
        of arguments. Please overwrite in inherited class.

        :param func_name: name of the function incorrectly called
        :type func_name: str
        :param exp_len: the number of arguments that should have been present
        :type exp_len: int
        :param passed: the arguments which were given
        :type passed: list
        """
        errorcode = "Implementation error!"
        + " This function (BaseParser._parser_handle_incorrect_argno)"
        + " should never be called directly, but should be overwritten by any"
        + " classes inheriting BaseParser."
        raise Exception(errorcode)

    def _parser_handle_conversion_error(self,func_name,argument,type,error):
        """ Virtual function for handling a runtime call which fails to convert
        an argument. Please overwrite in inherited class.

        :param func_name: name of the function incorrectly called
        :type func_name: str
        :param argument: the argument which failed conversion
        :type argument: str
        :param type: the function used to try and convert 'argument' to a
            particular type
        :type type: method
        :param error: the Exception thrown when conversion was attempted
        :type error: class: `Exception`
        """
        errorcode = "Implementation error!"
        + " This function (BaseParser._parser_handle_conversion_error)"
        + " should never be called directly, but should be overwritten by any"
        + " classes inheriting BaseParser."
        raise Exception(errorcode)

    def _parser_handle_func_result(self,result):
        """ Virtual function for handling a runtime call which succeeds.
        Please overwrite in inherited class.

        :param result: result returned by calling parsed function
        """
        errorcode = "Implementation error!"
        + " This function (BaseParser._parser_handle_func_result)"
        + " should never be called directly, but should be overwritten by any"
        + " classes inheriting BaseParser."
        raise Exception(errorcode)
