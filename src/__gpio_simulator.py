class MockGPIO:
    BCM = 'BCM'
    OUT = 'OUT'
    IN = 'IN'
    HIGH = 1
    LOW = 0

    _pin_modes = {}
    _pin_states = {}

    @classmethod
    def setmode(cls, mode):
        print(f"GPIO mode set to {mode}")
    
    @classmethod
    def setwarnings(cls, flag):
        cls._warnings = flag
        print(f"GPIO warnings set to {'on' if flag else 'off'}")

    @classmethod
    def setup(cls, pin, mode):
        if pin in cls._pin_modes and cls._warnings:
            print(f"Warning: Pin {pin} is being setup again.")
        cls._pin_modes[pin] = mode
        cls._pin_states[pin] = cls.LOW  # Default to LOW
        print(f"GPIO pin {pin} set up as {mode}")
        
    @classmethod
    def output(cls, pin, state):
        if pin in cls._pin_modes and cls._pin_modes[pin] == cls.OUT:
            cls._pin_states[pin] = state
            print(f"GPIO pin {pin} output set to {'HIGH' if state == cls.HIGH else 'LOW'}")
        else:
            print(f"Error: Pin {pin} is not set as OUTPUT.")

    @classmethod
    def input(cls, pin):
        if pin in cls._pin_modes and cls._pin_modes[pin] == cls.IN:
            return cls._pin_states[pin]
        else:
            print(f"Error: Pin {pin} is not set as INPUT.")
            return None

    @classmethod
    def cleanup(cls):
        cls._pin_modes.clear()
        cls._pin_states.clear()
        print("GPIO cleanup completed.")
