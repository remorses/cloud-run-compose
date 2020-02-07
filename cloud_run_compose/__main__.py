import fire
from .up import up
from .down import down

fire.Fire(dict(up=up, down=down))
