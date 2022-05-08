# enviroform.py: another terraform wrapper

## Background

The Terraform CLI can be used with a wide variety of workflows. Out of the box, you can get something deployed very quickly by running a `terraform init` and a `terraform apply`.

`enviroform.py` facilitates doing deploys in muliple cloud acounts, multiple regions, multiple environments. It wraps `terraform init` and `terraform <command>`, dynamically including the appropriate .tfvars input files that are needed. It establishes a pattern of organizing your terraform config and .tfvars files that is well-suited to a large cloud footprint.

Note: This script reflects how I've used terraform in large organizations over the past few years. However, things are ever-evolving. e.g. Terraform Cloud is a service that solves these problems (and more). This tool is oriented toward enhancing the experience of using Terraform CLI.

## Concepts

### Your terraform config

This script is meant to be run in the root of your terraform repo and for you to specify a relative path to the terraform config directory. It expects to find a main.tf file in that directory (and typically input variables defined). It expects that config directory to live in a parent directory which defines types of terraform configurations. You can name these as you like but a simple example would "apps" and "infra".

<your_path>/<config_type>/<config_name>/main.tf

### Your terraform input variables files, *environments*

You will also specify a relative path to your top level .tfvars file for the tf config that you want to deploy. This is where the file heirarchy that defines an *environment* comes in to play. An *environment* is a collection of related resources. We create a heirarchy of terraform tfvars files that reflect the heirarchy of an *environment* E.g. in AWS, these would exist in an AWS account. That account may have multiple regions under it. Each region will have it's own `backend.tfvars` (e.g. specifying an S3 bucket). In each region, you have your collection of terraform resources (which you can name arbitrarily, e.g. "apps" "infra")

Expects the following files to exist:
  - ```<your_path>/<environment>/environment.tfvars```
    - Environment-wide specific terraform variables
  - ```<your_path>/<environment>/<region>/backend.tfvars```
    - Environment specific terraform backend configuration
  - ```<your_path>/<environment>/<region>/region.tfvars```
    - region specific terraform variables (e.g. AWS region)
  - ```<your_path>/<environment>/<region>/<config_type>/<config_name>/<instance_name>.tfvars```
    - a .tfvars file to deploy an instance of the `<config_name>`, of `<config_type>` in `<region>`, of `<environment>`
    - Note: you can call this `default.tfvars`, but per the example folder, you may want to deploy multiple instances of a given resource so you could put other .tfvars files in this dir


This script will include all the right tfvars files when doing the following tf commands:
['plan', 'apply', 'refresh', 'destroy', 'import']

Otherwise it will will *terraform init* then only use your tf command and your args.

If you want to do a special tf init invocation (e.g. init -upgrade), this
script will include the correct backend.tfvars and then only run the
command and args as you provided them.

Perhaps the best way to understand all of this is to look at the Usage example below. At a high level, an invocation of enviroform.py interacts with one and only one terraform config and one and only one state file. It's primary job is to infer all of the details of *which* instance of a terraform config you want to deploy and where. The above file heirarchy is what "declares" the desired heirarchy in the cloud.

## Getting set up

TODO: let's add an 'init' command to make all this easier...

Study the *example* directory. Create your own directory structure and modify each .tfvars file appropriately

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

/usr/local/bin/terraform_1.0.2 init -backend-config=/Users/bneutra/dev/enviroform/example/environments/example-account/us-east-1/backend.tfvars -backend-config=key=apps/example-app/default/state.tfstate

/usr/local/bin/terraform_1.0.2 apply -var-file=/Users/bneutra/dev/enviroform/example/environments/example-account/environment.tfvars -var-file=/Users/bneutra/dev/enviroform/example/environments/example-account/us-east-1/region.tfvars -var-file=/Users/bneutra/dev/enviroform/example/environments/example-account/us-east-1/apps/example-app/default.tfvars

```

## Testing

```
pip3 install pytest
pytest .
```