# Contribution Guide

You shouldn't edit the node class files (all files under `diagrams/` directory) by
yourself.

## Set up your environment

- See [DEVELOPMENT][DEVELOPMENT.md]

## Resources

### Update nodes

All node classes are auto-generated from image resource files. For example, the
`diagram.aws.compute.EC2` class is auto-generated based on the
`resources/aws/compute/ec2.png` image resource file.

So, if you want to add new node resources or update existing node resources, you
can just add or update the image files in `resources/<provider>/<type>/<image>`.

Images should be resized to fit a maximum of 256 pixels wide or high.

```shell
# You can do that easily with ImageMagick
convert -resize 256 my_big_image.jpg my_image.jpg

# Or FFmpeg
ffmpeg -i my_big_image.jpg -vf scale=w=256:h=256:force_original_aspect_ratio=decrease my_image.png
```

Then just run the `./autogen.sh` to generate the added or updated node classes. (cf. [DEVELOPMENT][DEVELOPMENT.md])

> IMPORTANT NOTE: To run `autogen.sh`, you need the [round][round], [black][black] and
> [inkscape][inkscape] command line tools that are used for cleaning the image
> resource filenames and formatting the generated python code.
>
> macOS users can download inkscape via Homebrew.
>
> Or you can use the docker image.

[DEVELOPMENT.md]: ./DEVELOPMENT.md
[round]: https://github.com/mingrammer/round
[black]: https://pypi.org/project/black
[inkscape]: https://inkscape.org/ko/release

#### Update Specific Instructions for Azure Icons

Download and unzip [Azure Icons](https://learn.microsoft.com/en-us/azure/architecture/icons/)

Execute inside Azure_Public_Service_Icons/Icons/
```bash
# Rename some diretories
mv ai\ +\ machine\ learning/ aimachinelearning/
mv app\ services/ appservices
mv azure\ stack/ azurestack
mv azure\ ecosystem/ azureecosystem
mv management\ +\ governance/ managementgovernance
mv  mixed\ reality mixedreality
mv new\ icons/ newicons
#  Convert Name to name
rename -f 'y/A-Z/a-z/' ./*/*
# Create png files and eliminate ?????-icon-service from namefile
find . -type f -name "*.svg" -exec bash -c 'inkscape -h 256  --export-filename="${0%.svg}.png" "$0";mv "${0%.svg}.png" "$(echo "${0%.svg}.png" | sed -r 's/[0-9]{5}-icon-service-//')"' {} \;
# Delete svg files
find . -type f -name "*.svg" -exec bash -c 'rm "$0"' {} \;
```

If you get any errors with autogen, it will probably be a '+' in  filename

### Add new provider

To add a new provider to Diagrams, please follow the steps below in addition to the image intructions above:
- in `autogen.sh` add in the `providers` variable the new provider code
- in `config.py`:
  - in the `providers` variable, add the new provider code
  - in the `FILE_PREFIXES` variable, add a new entry with your new provider code. And eventually a file prefix
  - Optionnaly, update the `UPPER_WORDS` variable to a new entry with your new provider code.
  - in the `ALIASES` variable, add a new entry with your new provider code. See below on how to add new aliases.
- in `scripts/resource.py`:
  - add a function `cleaner_XXX` (replace XXX by your provider name). For the implementation look at the existing functions
  - in the `cleaners` variable, add an entry with your new provider code and the function defined above
- in `sidebars.json`, update the `Nodes` array to add the reference of the new provider
- in the `diagrams` folder, add a new file `__init__.py` for the new provider. For the content look at the existing providers

### Update Aliases

Some node classes have alias. For example, `aws.compute.ECS` class is an alias
of `aws.compute.ElasticContainerService` class. Aliases also were auto-generated
from `ALIASES` map in [config.py](config.py).

So, if you want to add new aliases or update existing aliases, you can just add
or update the `ALIASES` map in [config.py](config.py).

Then just run the `./autogen.sh` to generate the added or updated aliases. (cf. [DEVELOPMENT][DEVELOPMENT.md])

> IMPORTANT NOTE: To run `autogen.sh`, you need the [round][round] and
> [inkscape][inkscape] command line tools that are used for cleaning the image
> resource filenames.
>
> macOS users can download inkscape via Homebrew.
>
> Or you can use the docker image.

## Run Tests

```shell
python -m unittest tests/*.py -v
```

## Testing changes to the website

The [Docusaurus](https://docusaurus.io/)-based documentation website can be run by installing dependencies, then simply running `npm run start`.

```bash
cd website/
npm i
npm run start
```

The website will be available on [http://localhost:3000](http://localhost:3000).

Edit files in `website/` and `docs/` respectively to edit documentation.
