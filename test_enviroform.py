# Tests for test_enviroform.py
# run with pytest .

import argparse
import copy
import os
import enviroform
import unittest.mock as mock

patch = mock.patch

os.environ['TERRAFORM_EXECUTABLE'] = 'terraform'


def get_test_root_path():
    return enviroform.get_git_root_path()


os.chdir(get_test_root_path())


basic_args = argparse.Namespace()
basic_args.terraform_config_path = 'example/terraform/apps/example-app'
basic_args.tfvars_file_path = 'example/environments/example-account/us-east-1/apps/example-app/default.tfvars'  # NOQA
basic_args.dry_run = False


@patch('enviroform.Enviroform.call')
def test_apply(subprocess_mock):
    """Basic positive test case."""
    subprocess_mock.return_value = 0
    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        enviroform.get_tf_cmd(),
        get_test_root_path(),
        basic_args,
        ['apply'],
    )

    with patch.object(
        tf,
        'do_cmd',
        wraps=tf.do_cmd
    ) as patched:
        tf.run_tf_cmd()
        # 3 commands: rm .terraform, init, apply
        assert subprocess_mock.call_count == 3
        assert patched.mock_calls[0].args[0] == ['rm', '-rf', '.terraform']
        assert patched.mock_calls[1].args[0] == [
            'terraform',
            'init',
            f'-backend-config={root_path}/example/environments/example-account/us-east-1/backend.tfvars',  # NOQA
            '-backend-config=key=apps/example-app/default/state.tfstate'
        ]
        assert patched.mock_calls[2].args[0] == [
            'terraform',
            'apply',
            f'-var-file={root_path}/example/environments/example-account/environment.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/region.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/apps/example-app/default.tfvars',  # NOQA
        ]


@patch('enviroform.Enviroform.call')
def test_plan(subprocess_mock):
    """tf plan, special treatment."""
    subprocess_mock.return_value = 0
    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        enviroform.get_tf_cmd(),
        get_test_root_path(),
        basic_args,
        ['plan'],
    )

    with patch.object(
        tf,
        'do_cmd',
        wraps=tf.do_cmd
    ) as patched:
        tf.run_tf_cmd()
        # 3 commands: rm .terraform, init, apply
        assert subprocess_mock.call_count == 3
        assert patched.mock_calls[0].args[0] == ['rm', '-rf', '.terraform']
        assert patched.mock_calls[1].args[0] == [
            'terraform',
            'init',
            f'-backend-config={root_path}/example/environments/example-account/us-east-1/backend.tfvars',  # NOQA
            '-backend-config=key=apps/example-app/default/state.tfstate'
        ]
        assert patched.mock_calls[2].args[0] == [
            'terraform',
            'plan',
            f'-var-file={root_path}/example/environments/example-account/environment.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/region.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/apps/example-app/default.tfvars',  # NOQA
            '-detailed-exitcode'
        ]
        # make sure we request rc 0 and 2 are allowed for plan
        assert patched.mock_calls[2].args[1] == [0, 2]


@patch('enviroform.Enviroform.call')
def test_init(subprocess_mock):
    """tf init, special treatment."""
    subprocess_mock.return_value = 0
    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        enviroform.get_tf_cmd(),
        get_test_root_path(),
        basic_args,
        ['init'],
    )

    with patch.object(
        tf,
        'do_cmd',
        wraps=tf.do_cmd
    ) as patched:
        try:
            tf.run_tf_cmd()
        except SystemExit as err:
            assert "You specified init, so we will stop here. exit." in err.args[0]  # NOQA

        # 3 commands: rm .terraform, init, apply
        assert subprocess_mock.call_count == 2
        assert patched.mock_calls[0].args[0] == ['rm', '-rf', '.terraform']
        assert patched.mock_calls[1].args[0] == [
            'terraform',
            'init',
            f'-backend-config={root_path}/example/environments/example-account/us-east-1/backend.tfvars',  # NOQA
            '-backend-config=key=apps/example-app/default/state.tfstate'
        ]


@patch('enviroform.Enviroform.call')
def test_output(subprocess_mock):
    """tf output, no tfvars."""
    subprocess_mock.return_value = 0
    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        enviroform.get_tf_cmd(),
        get_test_root_path(),
        basic_args,
        ['output'],
    )

    with patch.object(
        tf,
        'do_cmd',
        wraps=tf.do_cmd
    ) as patched:
        tf.run_tf_cmd()
        # 3 commands: rm .terraform, init, apply
        assert subprocess_mock.call_count == 3
        assert patched.mock_calls[0].args[0] == ['rm', '-rf', '.terraform']
        assert patched.mock_calls[1].args[0] == [
            'terraform',
            'init',
            f'-backend-config={root_path}/example/environments/example-account/us-east-1/backend.tfvars',  # NOQA
            '-backend-config=key=apps/example-app/default/state.tfstate'
        ]
        assert patched.mock_calls[2].args[0] == [
            'terraform',
            'output',
        ]


@patch('enviroform.Enviroform.call')
def test_failed_tf_cmd(subprocess_mock):
    """When commands fail."""
    subprocess_mock.return_value = 1

    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        root_path,
        enviroform.get_git_root_path(),
        basic_args,
        ['apply'],
    )
    try:
        tf.run_tf_cmd()
        assert None == "run_tf_cmd should have raised an exception"
    except Exception as err:
        assert "Command failed with rc 1" in err.args[0]


@patch('enviroform.Enviroform.call')
def test_expect_non_zero(subprocess_mock):
    """do_cmd does not raise when told to not raise."""
    # example is for tf plan which returns 2 if no diff
    subprocess_mock.return_value = 2

    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        root_path,
        enviroform.get_git_root_path(),
        basic_args,
        ['apply'],
    )
    tf.process_args()
    rc = tf.do_cmd(['whatever', 'one', 'two'], expected_rcs=[0, 2])
    assert rc == 2


dry_args = copy.deepcopy(basic_args)
dry_args.dry_run = True


@patch('enviroform.Enviroform.call')
def test_dry(subprocess_mock):
    """--dry-run positive test case."""
    subprocess_mock.return_value = 0
    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        enviroform.get_tf_cmd(),
        get_test_root_path(),
        dry_args,
        ['apply'],
    )

    with patch.object(
        tf,
        'do_cmd',
        wraps=tf.do_cmd
    ) as patched:
        tf.run_tf_cmd()
        # 3 commands: rm .terraform, init, apply
        assert subprocess_mock.call_count == 0  # no actual calls though
        assert patched.mock_calls[0].args[0] == ['rm', '-rf', '.terraform']
        assert patched.mock_calls[1].args[0] == [
            'terraform',
            'init',
            f'-backend-config={root_path}/example/environments/example-account/us-east-1/backend.tfvars',  # NOQA
            '-backend-config=key=apps/example-app/default/state.tfstate'
        ]
        assert patched.mock_calls[2].args[0] == [
            'terraform',
            'apply',
            f'-var-file={root_path}/example/environments/example-account/environment.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/region.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/apps/example-app/default.tfvars',  # NOQA
        ]


no_deployable_args = copy.deepcopy(basic_args)
no_deployable_args.terraform_config_path = 'example/terraform/apps/example-foo'


@patch('enviroform.Enviroform.call')
def test_no_config(subprocess_mock):
    """Invalid deployable dir."""

    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        root_path,
        enviroform.get_git_root_path(),
        no_deployable_args,
        ['apply'],
    )
    try:
        tf.run_tf_cmd()
        assert None == "run_tf_cmd should have raised an exception"
    except SystemExit as err:
        assert "dir not found" in str(err.code)


wrong_vars_args = argparse.Namespace()
wrong_vars_args.terraform_config_path = 'example/terraform/infra/example-networking'  # NOQA
wrong_vars_args.tfvars_file_path = 'example/environments/example-account/us-east-1/apps/example-app/default.tfvars'  # NOQA
wrong_vars_args.dry_run = False


@patch('enviroform.Enviroform.call')
def test_wrong_vars(subprocess_mock):
    """Invalid tfvars file."""

    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        root_path,
        enviroform.get_git_root_path(),
        wrong_vars_args,
        ['apply'],
    )
    try:
        tf.run_tf_cmd()
        assert None == "run_tf_cmd should have raised an exception"
    except SystemExit as err:
        assert "ERROR: tfvars dir should match the config name: example-networking but is: example-app" == err.code  # NOQA


instance_args = argparse.Namespace()
instance_args.terraform_config_path = 'example/terraform/apps/example-app'
instance_args.tfvars_file_path = 'example/environments/example-account/us-east-1/apps/example-app/experiment.tfvars'  # NOQA
instance_args.dry_run = False


@patch('enviroform.Enviroform.call')
def test_instance(subprocess_mock):
    """Test a different instance of a deployable."""
    subprocess_mock.return_value = 0
    root_path = get_test_root_path()
    tf = enviroform.Enviroform(
        enviroform.get_tf_cmd(),
        get_test_root_path(),
        instance_args,
        ['apply'],
    )

    with patch.object(
        tf,
        'do_cmd',
        wraps=tf.do_cmd
    ) as patched:
        tf.run_tf_cmd()
        # 3 commands: rm .terraform, init, apply
        assert subprocess_mock.call_count == 3
        assert patched.mock_calls[0].args[0] == ['rm', '-rf', '.terraform']
        assert patched.mock_calls[1].args[0] == [
            'terraform',
            'init',
            f'-backend-config={root_path}/example/environments/example-account/us-east-1/backend.tfvars',  # NOQA
            '-backend-config=key=apps/example-app/experiment/state.tfstate'
        ]
        assert patched.mock_calls[2].args[0] == [
            'terraform',
            'apply',
            f'-var-file={root_path}/example/environments/example-account/environment.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/region.tfvars',  # NOQA
            f'-var-file={root_path}/example/environments/example-account/us-east-1/apps/example-app/experiment.tfvars',  # NOQA
        ]
