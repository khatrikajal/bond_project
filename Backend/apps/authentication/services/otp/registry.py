from .strategies.dummy import DummyOtpStrategy
from .strategies.email.gmail import GmailOtpStrategy


class OtpStrategyRegistry:
    _registry = {}

    @classmethod
    def register(cls, name: str, strategy_cls):
        cls._registry[name] = strategy_cls

    @classmethod
    def get_strategy(cls, name: str):
        strategy_cls = cls._registry.get(name)
        if not strategy_cls:
            raise ValueError(f"OTP Strategy '{name}' not registered.")
        return strategy_cls()

    @classmethod
    def list_strategies(cls):
        return list(cls._registry.keys())


# Register during import
OtpStrategyRegistry.register("dummy", DummyOtpStrategy)
OtpStrategyRegistry.register("gmail", GmailOtpStrategy)
