import importlib
import pkgutil

from typer import Typer


def load_plugins(app: Typer, package_name: str) -> list[str]:
    """
    Dynamically loads Typer commands and groups from the specified package.
    Expects each plugin module to have a `register(app: Typer)` function.
    """
    loaded_plugins = []  # type: ignore

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return loaded_plugins

    if not hasattr(package, "__path__"):
        return loaded_plugins

    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        full_module_name = f"{package_name}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
            if hasattr(module, "register") and callable(module.register):
                module.register(app)
                loaded_plugins.append(full_module_name)
        except Exception:
            pass  # In a real app we'd log this, but for now we swallow it or print a warning

    return loaded_plugins
