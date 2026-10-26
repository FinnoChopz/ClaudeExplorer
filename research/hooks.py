"""Hook lifetime management; importable without a neural dependency."""
from contextlib import contextmanager


@contextmanager
def temporary_hooks(pairs):
    handles = []
    try:
        for module, hook in pairs:
            handles.append(module.register_forward_hook(hook))
        yield
    finally:
        for handle in reversed(handles):
            handle.remove()


def hidden_output(output):
    return output[0] if isinstance(output, tuple) else output


def replace_hidden(output, hidden):
    return (hidden, *output[1:]) if isinstance(output, tuple) else hidden


def last_token_patch(vector):
    def inject(module, inputs, output):
        hidden = hidden_output(output).clone()
        hidden[:, -1, :] = vector
        return replace_hidden(output, hidden)
    return inject
