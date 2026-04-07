import click


class IntListOrInt(click.ParamType):
    name = "int_or_list"

    def convert(self, value, param, ctx):
        try:
            # Try plain integer first: --multipoints=2
            return [int(value)]
        except ValueError:
            pass
        try:
            # Try list format: --multipoints=[0,2] or --multipoints=0,2
            cleaned = value.strip().strip('[]')
            return [int(x.strip()) for x in cleaned.split(',')]
        except ValueError:
            self.fail(f"'{value}' is not a valid integer or list of integers", param, ctx)