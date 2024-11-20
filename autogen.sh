#!/bin/bash

app_root_dir="diagrams"

# NOTE: azure icon set is not latest version
providers=(
  "onprem"
  "aws"
  "azure"
  "digitalocean"
  "gcp"
  "ibm"
  "firebase"
  "k8s"
  "alibabacloud"
  "oci"
  "programming"
  "saas"
  "elastic"
  "generic"
  "openstack"
  "outscale"
)

if ! [ -x "$(command -v round)" ]; then
  echo 'round is not installed'
  exit 1
fi

if ! [ -x "$(command -v inkscape)" ]; then
  echo 'inkscape is not installed'
  exit 1
fi

if ! [ -x "$(command -v convert)" ]; then
  echo 'image magick is not installed'
  exit 1
fi

if ! [ -x "$(command -v black)" ]; then
  echo 'black is not installed'
  exit 1
fi

# preprocess the resources
for pvd in "${providers[@]}"; do
  # convert the svg to png for azure provider
  if [ "$pvd" = "onprem" ] || [ "$pvd" = "azure" ]; then
    echo "converting the svg to png using inkscape for provider '$pvd'"
    python -m scripts.resource svg2png "$pvd"
  fi
  if [ "$pvd" == "oci" ] || [ "$pvd" = "ibm" ]; then
    echo "converting the svg to png using image magick for provider '$pvd'"
    python -m scripts.resource svg2png2 "$pvd"
  fi
  echo "cleaning the resource names for provider '$pvd'"
  python -m scripts.resource clean "$pvd"
  # round the all png images for aws provider
  if [ "$pvd" = "aws" ]; then
    echo "rounding the resources for provider '$pvd'"
    python -m scripts.resource round "$pvd"
  fi
done

# generate the module classes and docs
for pvd in "${providers[@]}"; do
  echo "generating the modules & docs for provider '$pvd'"
  python -m scripts.generate "$pvd"
done

# Generate doc for custom module
echo "generating the docs for custom"
python -m scripts.generate "custom"

# copy icons across to website
echo "copying icons to website static folder"
cp -r resources website/static/img/

# run black
echo "linting the all the diagram modules"
black "$app_root_dir"/**/*.py
