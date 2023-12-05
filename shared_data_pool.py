class DataPool:

    prices_pool = []

    @classmethod
    def return_dp(cls):
        return cls.prices_pool.copy()

    @classmethod
    def append_dp(cls, data):
        cls.prices_pool.append(data)

    @classmethod
    def clear_dp(cls):
        cls.prices_pool.clear()

