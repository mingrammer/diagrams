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
