class BaseScenario:
    def __init__(self, name: str, description: str, max_turns: int):
        self.name = name
        self.description = description
        self.max_turns = max_turns

    def get_buyer_params(self) -> dict:
        raise NotImplementedError

    def get_seller_params(self) -> dict:
        raise NotImplementedError
        
    def get_initial_state(self) -> dict:
        return {}
