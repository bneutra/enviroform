# enviroform.py: another terraform wrapper

## Background

The Terraform CLI provides the core functionality for deploying a terraform config i.e. by executing a `terraform init` and a `terraform apply`.

`enviroform.py` facilitates doing deploys in muliple cloud acounts, multiple regions and multiple environments. It wraps `terraform init` and `terraform <command>` dynamically including the appropriate `.tfvars` input files that are needed. It establishes a pattern of organizing your terraform config and `.tfvars` files that is well-suited to a large cloud footprint.

Note: This script reflects how I've used terraform in large organizations over the past few years. However, things are ever-evolving. e.g. Terraform Cloud is a service that solves these problems (and more). This tool is oriented toward enhancing the experience of using Terraform CLI.

## Concepts

### Your terraform config

This script is meant to be run in the root of your terraform repo and for you to specify a relative path to the terraform config directory. It expects to find a main.tf file in that directory. Typically, input variables are defined to allow you to re-use that terraform config in multiple contexts. It expects that config directory to live in a parent directory which defines types of terraform configs. You can name these as you like but a simple example would "apps" and "infra".

`<your_path>/<config_type>/<config_name>/main.tf`

### Your terraform input variables files organized in *environments*

You will also specify a relative path to your top level `.tfvars` file for the terraform config that you want to deploy. This is where the file heirarchy that defines an *environment* comes in to play. An *environment* is a collection of related resources. We create a heirarchy of terraform `.tfvars` files that reflect the heirarchy of an *environment* e.g. in AWS, resources might be grouped in an AWS account. That account may have multiple regions under it. Each region will have its own `backend.tfvars` (e.g. specifying an S3 bucket). In each region, you may have any number of AWS resources that are deployed via terrraform configs: `<config_name>`. Those are organized in folders reflecting arbitrarily defined categories: `<config_type>`. Finally, there can be N number of instances of a terraform config each having a `.tfvars` file containing the input variables that define it: `<instance_name>.tfvars`.

As such, `enviroform.py` expects the following files to exist:
  - `<your_path>/<environment>/environment.tfvars`
    - Environment-wide specific terraform variables
  - `<your_path>/<environment>/<region>/backend.tfvars`
    - Environment specific terraform backend configuration
  - `<your_path>/<environment>/<region>/region.tfvars`
    - region specific terraform variables (e.g. AWS region)
  - `<your_path>/<environment>/<region>/<config_type>/<config_name>/<instance_name>.tfvars`
    - a `.tfvars` file to deploy an instance of the `<config_name>`, of `<config_type>` in `<region>`, of `<environment>`
    - Note: you can call this `default.tfvars` by convention but if you ever want to have more than one instance of a particular terraform config, just note that the terraform state 'key' is named after that `<instance_name>` and you should take care to provide an input variable to allows the terraform config to uniquely name each instance's resources.

In summary, this script will collect and include all the needed `.tfvars` files when doing the following commonly used terraform commands:
- plan
- apply
- refresh
- destroy
- import

For other commands, it will will *terraform init* then just use the command and args that you provide.

If you want to do a special tf init invocation (e.g. init -upgrade), this script will include the correct backend.tfvars and only run the init command and args as you provided them.

Perhaps the best way to understand all of this is to look at the `Usage` example below. At a high level, an invocation of `enviroform.py` interacts with one and only one terraform config and one and only one state file, providing the relevant `.tfvars` files that it discovers in the `environments` directory.

## Getting set up

TODO: let's add an 'init' command to make all this easier...

Study the *example* directory. Create your own directory structure and modify each `.tfvars` file appropriately

## Usage

*enviroform.py* does not handle cloud credentials. It assumes that the command line environment is already set up to acceess the cloud environment you are using (e.g. AWS_PROFILE is set properly, etc). You should authenticate to the cloud account where you want to deploy to and where your backend.tfvars backend lives.

Install a virtualenv:
```
python3 -m venv .venv
source .venv/bin/activate
```

Help:
```
$ python3 enviroform.py --help

usage: enviroform.py [-h] [--terraform-config-path TERRAFORM_CONFIG_PATH]
                     [--tfvars-file-path TFVARS_FILE_PATH] [--dry-run]

enviroform.py: a terraform wrapper script.

optional arguments:
  -h, --help            show this help message and exit
  --terraform-config-path TERRAFORM_CONFIG_PATH, -t TERRAFORM_CONFIG_PATH
                        path to terraform config directory
  --tfvars-file-path TFVARS_FILE_PATH, -z TFVARS_FILE_PATH
                        path to .tfvars directory
  --dry-run, -d         dry run


```

Example --dry-run (does nothing, no credentials required, shows what the script *would* do):
```
$ python3 enviroform.py -t example/terraform/apps/example-app \
-z example/environments/example-account/us-east-1/apps/example-app/default.tfvars \
--dry-run apply

==== Executing in --dryrun mode ===

rm -rf .terraform

terraform init -backend-config=/Users/bneutra/dev/enviroform/example/environments/example-account/us-east-1/backend.tfvars -backend-config=key=apps/example-app/default/state.tfstate

terraform apply -var-file=/Users/bneutra/dev/enviroform/example/environments/example-account/environment.tfvars -var-file=/Users/bneutra/dev/enviroform/example/environments/example-account/us-east-1/region.tfvars -var-file=/Users/bneutra/dev/enviroform/example/environments/example-account/us-east-1/apps/example-app/default.tfvars

```

## Testing

```
pip3 install pytest
pytest .
```