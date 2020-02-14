#!/bin/bash
app_root_dir="diagrams"

# NOTE: azure icon set is not latest version
providers=("aws" "azure" "gcp" "k8s")

if ! [ -x "$(command -v round)" ]; then
  echo 'round is not installed'
fi

if ! [ -x "$(command -v inkscape)" ]; then
  echo 'inkscape is not installed'
fi

# preprocess the resources
for pvd in "${providers[@]}"; do
  # convert the svg to png for azure provider
  if [ "$pvd" = "azure" ]; then
    echo "converting the svg to png for provider '$pvd'"
    python -m scripts.resource svg2png "$pvd"
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

# run black
echo "linting the all the diagram modules"
black "$app_root_dir"/**/*.py
