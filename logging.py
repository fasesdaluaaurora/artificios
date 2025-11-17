# no inicio:

import logging.basicConfig(
  level=logging.DEBUG,
  format=%(asctime)s [%(name)s]: %(message)s",
  datefmt="%Y-%m-%d %H:%M:%S"
)

#em cada arquivo:
# script isolado
import os
import logging
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

# fluxo de execução

logger = logging.getLogger(__name__)

# no apontamento:

coisa="fofa"
linguagem="python"
logger.info("qualquer coisa em %s é $s", coisa, linguagem)
