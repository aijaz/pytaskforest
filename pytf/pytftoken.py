from attrs import define
import logging
import os
import pathlib

import tomlkit


@define
class PyTfToken:
    name: str
    num_instances: int

    @staticmethod
    def update_token_usage(config):
        token_file = os.path.join(config.log_dir, "token_usage.toml")
        if not os.path.exists(token_file):
            return

        token_file_text = pathlib.Path(token_file).read_text()
        token_usage_doc = tomlkit.loads(token_file_text)

        if not token_usage_doc.get('token'):
            return

        new_token_doc:tomlkit.TOMLDocument = tomlkit.document()
        aot = None

        for token in token_usage_doc['token']:
            # expect token name, info file
            info_file_path = token['info_file_path']
            info_doc = tomlkit.loads(pathlib.Path(info_file_path).read_text())
            if info_doc.get('error_code') is not None:
                # no longer running
                if aot is None:
                    aot = tomlkit.aot()
                aot.append(token)

        if aot is None:
            os.remove(token_file)
            return

        new_token_doc.append('token', aot)
        with open(token_file, "w") as f:
            f.write(tomlkit.dumps(new_token_doc))

    @staticmethod
    def consume_token(config, token_names, info_file_path) -> bool:
        logger = logging.getLogger('pytf_logger')

        for name in token_names:
            if config.tokens_by_name.get(name) is None:
                logger.error(f"Unknown Token: {name}")
                return False

        token_file = os.path.join(config.log_dir, "token_usage.toml")
        if not os.path.exists(token_file):
            with open(token_file, "w") as f:
                f.write("")

        current_usage:[str,int] = {}
        token_usage_doc = tomlkit.loads(pathlib.Path(token_file).read_text())

        for token in token_usage_doc.get('token', []):
            token_name_in_usage = token['token_name']
            current_usage[token_name_in_usage] = current_usage.get(token_name_in_usage, 0) + 1

        logger.info(f"{current_usage=}")

        for token_name in token_names:
            tok = config.tokens_by_name.get(token_name)

            total_num_tokens = tok.num_instances

            if current_usage.get(token_name, 0) < total_num_tokens:
                t = tomlkit.table()
                t['token_name'] = token_name
                t['info_file_path'] = info_file_path

                token_usage_doc['token'].append(t)
            else:
                logger.warning(f"Couldn't find available token: {token_name}")
                return False

        with open(token_file, "w") as f:
            f.write(tomlkit.dumps(token_usage_doc))

        logger.info("All tokens available")
        return True
