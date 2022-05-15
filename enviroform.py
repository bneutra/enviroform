#!/usr/bin/env python3
"""
  Usage:
  enviroform.py -t <terraform_path> -z <tfvars_path> <tf_command> [<options>]

  Runs the tf <tf_command> (with tf <options>) for the terraform config
  found in <terraform_path>. See README.md for details.
"""

import argparse
import os
import sys
import subprocess


class Enviroform:
    """
    Wraps the series of steps required to run a terraform command.
    See main() for an implementation example
    """

    def __init__(
        self,
        terraform_path: str,
        root_path: str,
        known_args: argparse.Namespace,
        other_args: list
    ) -> None:

        self.terraform_path = terraform_path
        self.known_args = known_args
        self.other_args = other_args
        self.root_path = root_path
        self.environ = os.environ
        # tf apply can take a long time (e.g. db creation)
        # but 1 hour seems reasonable to just give up
        self.subprocess_timeout = 3600

    def check_file(self, fpath: str) -> None:
        """Raises SystemExit if file does not exit."""
        if not os.path.isfile(fpath):
            raise SystemExit(
                f'ERROR: file not found at: {fpath}. '
                f'Your root is {self.root_path}'
            )

    def check_dir(self, dpath: str) -> None:
        """Raises SystemExit if dir does not exit."""
        if not os.path.isdir(dpath):
            raise SystemExit(
                f'ERROR: dir not found at: {dpath}'
                f'Your root is {self.root_path}'
            )

    def call(self, cmd_list: list) -> int:
        """Wraps Popen using communicate, returns return code."""
        stderr = sys.stderr
        stdout = sys.stdout

        prc = subprocess.Popen(
            cmd_list,
            stdout=stdout,
            stderr=stderr,
            env=self.environ
        )
        prc.communicate(timeout=self.subprocess_timeout)
        # TODO: ^ this should work if the user sends a signal e.g. ctrl-c
        # tf can be tricky to stop, requiring multiple attempts by the user
        # But I believe communicate() will send that signal down to all
        # processes and allow the user to keep sending more signals if needed
        # If that doesn't work, the below approach may be explored
        # try:
        #     prc.communicate(timeout=self.subprocess_timeout)
        # except KeyboardInterrupt:
        #     print('Detected KeyboardInterrupt, killing process')
        #     # TODO: should we try several times?
        #     prc.kill()

        ret = prc.returncode

        return ret

    def do_cmd(self, cmd_list: list, expected_rcs: list = [0]) -> int:
        """Executes any shell command, returns return code."""
        print(' '.join(cmd_list))
        rc = 0
        if self.dry_run:
            print()
        else:
            rc = self.call(cmd_list)
        if rc not in expected_rcs:
            raise Exception(f'Command failed with rc {rc}')
        return rc

    def process_default_flags(self) -> None:
        """Validate/process default flags."""
        self.dry_run = self.known_args.dry_run
        tf_config_rel_path = self.known_args.terraform_config_path
        self.tf_config_path = os.path.join(
            self.root_path, tf_config_rel_path
        )
        self.check_dir(self.tf_config_path)

    def process_user_args(self) -> None:
        """Validate/process default args."""
        other_args = self.other_args
        if len(other_args) == 0:
            raise SystemExit(
                'ERROR: You must provide a terraform command e.g. apply'
            )
        self.tf_command = other_args[0]
        self.tf_args = other_args[1:]
        self.special_commands = [
            'plan', 'apply', 'refresh', 'destroy', 'import', 'init'
        ]
        if self.tf_command not in self.special_commands:
            print(
                f'\nWARNING:\nterraform {" ".join(other_args)}\n'
                'will be run as provided after init. '
                'It has no special processing. of tfvars files.'
                'You must provide all args and flags.\n'
            )

    def process_tfvars(
        self, tfvars_file_path: str
    ) -> tuple[list[str], list[str]]:
        """Generate terraform vars by inference."""

        tfvars_file_path = os.path.join(
            self.root_path, tfvars_file_path
        )
        self.check_file(tfvars_file_path)
        self.check_file(os.path.join(self.tf_config_path, 'main.tf'))

        # discover var files.
        # tfvars_file_path is split apart to infer the location of the
        # environment, backend, and region tfvars files
        # tf_config_path should have a parent directory that denotes
        # the config_type.
        tfvars_path_components = tfvars_file_path.split(os.sep)
        environments_base_path = os.sep.join(tfvars_path_components[:-5])
        env, region, tfvars_config_type, tfvars_dir, tfvars_filename = tfvars_path_components[len(tfvars_path_components)-5:]  # NOQA
        tf_config_path_components = self.tf_config_path.split(os.sep)
        config_type, config_name = tf_config_path_components[-2:]

        env_tfvars_file_path = os.path.join(
            environments_base_path, env, 'environment.tfvars')
        backend_tfvars_file_path = os.path.join(
            environments_base_path, env, region, 'backend.tfvars')
        region_tfvars_file_path = os.path.join(
            environments_base_path, env, region, 'region.tfvars')

        # validate that our tfvars files are where we expect
        self.check_file(env_tfvars_file_path)
        self.check_file(backend_tfvars_file_path)
        self.check_file(region_tfvars_file_path)
        instance_label = tfvars_filename.split('.')[0]
        if tfvars_dir != config_name:
            raise SystemExit(
                'ERROR: tfvars dir should match the config name: ' +
                f'{config_name} but is: {tfvars_dir}'
            )
        if tfvars_config_type != config_type:
            raise SystemExit(
                'ERROR: containing dir should match the config type: ' +
                f'{config_type} but is: {tfvars_config_type}'
            )
        backend_key = f'{config_type}/{config_name}/{instance_label}/state.tfstate'  # NOQA
        backend_args = [
            f'-backend-config={backend_tfvars_file_path}',
            f'-backend-config=key={backend_key}'
        ]
        var_file_args = [
            f'-var-file={env_tfvars_file_path}',
            f'-var-file={region_tfvars_file_path}',
            f'-var-file={tfvars_file_path}'
        ]
        return backend_args, var_file_args

    def process_args(self) -> None:
        """Process all flags and args."""
        self.process_user_args()
        self.process_default_flags()
        # NOTE: This implementation of finding .tfvars files on disk could.
        # be replaced with a different strategy, using subclassing.
        # e.g. pulling .tfvars variables from cloud state, instead.
        # like AWS Parameter Store
        self.backend_args, self.var_file_args = self.process_tfvars(self.known_args.tfvars_file_path)  # NOQA

    def run_tf_cmd(self) -> int:
        """
        Runs commands to execute various terraform commands,
        providing inferential support where needed.
        Returns: Integer, tf return code.
        """
        self.process_args()
        if self.dry_run:
            print('\n==== Executing in --dryrun mode ===\n')
        # tf init
        os.chdir(self.tf_config_path)
        self.do_cmd(
            ['rm', '-rf', '.terraform']
        )

        init_cmd = [self.terraform_path, 'init']
        init_cmd.extend(self.backend_args)
        if self.tf_command == 'init':
            # allow the user to run 'init' with their own args
            init_cmd.extend(self.tf_args)
            self.do_cmd(init_cmd)
            raise SystemExit("You specified init, so we will stop here. exit.")

        else:
            self.do_cmd(init_cmd)

        # tf command
        expected_rcs = [0]
        if self.tf_command == 'plan':
            # rc 0 means no diff was seen, rc 2 means diff
            self.tf_args.append('-detailed-exitcode')
            expected_rcs = [0, 2]

        cmd = [self.terraform_path, self.tf_command]
        cmd.extend(self.var_file_args)
        cmd.extend(self.tf_args)
        # let the user do something special
        if self.tf_command not in self.special_commands:
            print(
                f'Non-default command: "{self.tf_command}" '
                'executing without modification.\n'
            )
            cmd = [
                self.terraform_path,
                self.tf_command
            ] + self.tf_args
        return self.do_cmd(cmd, expected_rcs)


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    """
    Parses command line args to be passed to Enviroform
    Returns: a tuple of two objects:
      - argparse object with processed/known flags
      - list of strings containing remaining args
    """
    parser = argparse.ArgumentParser(
        description='enviroform.py: a terraform wrapper script.'
    )
    parser.add_argument(
        '--terraform-config-path',
        '-t',
        help='path to terraform config directory'
    )
    parser.add_argument(
        '--tfvars-file-path',
        '-z',
        help='path to your primary .tfvars file'
    )
    parser.add_argument(
        '--dry-run',
        '-d',
        action='store_true',
        help='dry run'
    )
    return parser.parse_known_args()


def get_git_root_path() -> str:
    """Returns the root path of the git repo that is."""
    git_cmd = ["git", "rev-parse", "--show-toplevel"]
    return subprocess.check_output(git_cmd).rstrip().decode('ascii')


def get_tf_cmd() -> str:
    """Returns the terraform command path to use."""
    # You can over-ride the default command 'terraform'
    # by setting this env var
    tf_cmd = os.environ.get('TERRAFORM_EXECUTABLE')
    if not tf_cmd:
        tf_cmd = 'terraform'
    return tf_cmd


def main() -> int:
    """Implement Enviroform as a script. Returns return code."""
    known_args, other_args = parse_args()
    sys.exit(
        Enviroform(
            get_tf_cmd(),
            get_git_root_path(),
            known_args,
            other_args
        ).run_tf_cmd())


if __name__ == '__main__':
    main()
