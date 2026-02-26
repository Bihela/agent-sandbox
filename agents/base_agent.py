class Agent:
    def __init__(self, name: str):
        self.name = name

    def decide_action(self, state: dict) -> dict:
        """
        Decide the next action based on the current world state.
        Must return a dictionary containing the action details.
        """
        raise NotImplementedError("Subclasses must implement let decide_action")
