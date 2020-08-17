import readline
import colorama
colorama.init()
import sys
import inputparser

class InteractivePrompt(inputparser.BaseParser):
    """ Base class for interactive input prompt utilising readline

    :param header_text: text to display at top of input
        whenever screen is cleared
    :type header_text: str
    :param function_dict: dictionary holding all functions that may be called
    :type function_dict: dict
    :param offset:
    :type offset: int
    :param protected_key: a key that under no circumstances should the user
        press, which is inserted before every macro to turn protected mode on
        to ensure macro infinite loops don't occur,
        defaults to "\n"
    :type protected_key: str, Optional
    """
    def __init__(self,header_text,function_dict,offset,protected_key="\n"):
        """ Constructor method
        """
        super(InteractivePrompt,self).__init__(offset)
        self._protected_key = protected_key
        self.header_text = header_text
        self._function_dict = function_dict
        self._function_dict["ls"] = self.ls
        self._function_dict["exit"] = self.exit
        self._bound_keys = {}
        readline.parse_and_bind('"{}": complete'.format(protected_key))
        #Use readline's complete functionality to safely input functions
        def completer(text,state):
            self.protected_mode_on()
        readline.set_completer(completer)
        self._protected_toggle = False
        self.close = False

    def __del__(self):
        """ Ensure bindings don't remain after closing
        """
        self.unbind_all()

    #running functions
    def run(self):
        """ Runs the interactive prompt until self.close == True
        """
        print(colorama.Back.GREEN
            + colorama.Fore.BLACK
            + self.header_text
            + colorama.Style.RESET_ALL)
        while not self.close:
            try:
                self._run_once()
                print(colorama.Style.RESET_ALL)
            except:
                print(colorama.Style.RESET_ALL)
                raise

    def _run_once(self):
        """ A single input iteration of the prompt
        """
        self.run_once_preprocessing()
        self.protected_mode_off()
        command = raw_input()
        for key in self._function_dict:
            if " "+key in command or command[:len(key)] == key:
                self._function_dict[key]()
                return
        self.no_command_return(command)

    def run_once_preprocessing(self):
        """ Virtual function to be overwritten.
        Any processing that needs to be done before calling raw_input()
            for every input.
        """
        raise Exception("InteractivePrompt.run_once_preprocessing should be"
            + " overwritten in inheriting class!")

    #protected mode togglers
    def protected_mode_on(self):
        """ Activates protected mode. Used to ensure no readline infinite loops
        """
        self._protected_toggle = True
        for key in self._bound_keys:
            readline.parse_and_bind('"{}": self-insert'.format(key))

    def protected_mode_off(self):
        """ Deactivates protected mode. Bound keys will work.
        """
        self._protected_toggle = False
        for key in self._bound_keys:
            command = self._bound_keys[key]
            readline.parse_and_bind('"{}": " {}{}()\\r'.format(
                key,
                self._protected_key,
                command))

    #binding functions
    def bind(self,key,command):
        """ Binds the given key to the decorated command

        :param key: the key to bind
        :type key: str
        :param command: the name of the command to call
        :type command: str
        """
        if self._protected_key not in key:
            self._bound_keys[key] = command
        else:
            raise Exception("Protected key found in bind key {}".format(key))

    def unbind(self,key):
        """ Unbinds the given key

        :param key: the key to unbind
        :type key: str
        """
        readline.parse_and_bind('"{}": self-insert'.format(key))
        del self._bound_keys[key]

    def unbind_all(self):
        """ Unbinds all bound keys
        """
        while len(self._bound_keys) > 0:
            self.unbind(self._bound_keys.keys()[0])

    #Screen manipulation
    def clear_screen(self):
        """ Clears the screen, then redisplays the header
        """
        sys.stderr.write("\x1b[2J\x1b[H")
        print(colorama.Back.GREEN
            + colorama.Fore.BLACK
            + self.header_text
            + colorama.Style.RESET_ALL)

    #For adding to func dict
    def exit(self):
        """ Exits the dialogue
        """
        self.close = True

    def ls(self):
        """ Lists all available functions
        """
        for key in self._function_dict:
            if key[0] != "_":
                print key+"\t",
