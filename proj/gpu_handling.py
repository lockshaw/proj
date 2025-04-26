from . import subprocess_trace as subprocess
import logging

_l = logging.getLogger(__name__)

def check_if_machine_supports_cuda() -> bool:
    try:
        subprocess.check_call(['nvidia-smi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        _l.info('Could not find executable nvidia-smi in path')
        return False
    except subprocess.CalledProcessError:
        _l.info('nvidia-smi returned nonzero error code')
        return False
