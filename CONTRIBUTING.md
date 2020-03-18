# Contribution Guide

You shouldn't edit the node class files (all files under `diagram` directory) by
yourself.

## Resources

### Update nodes

All node classes was auto-generated from image resource files. For example, the
`diagram.aws.compute.EC2` class was auto-generated based on
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

Then just run the `./autogen.sh` to generate the added or updated node classes.

> IMPORTANT NOTE: To run `autogen.sh`, you need [round][round] and
> [inkscape][inkscape] command lines that are used for clearning the image
> resource filenames.
>
> macOS users can download the inkscape via Homebrew.

[round]: https://github.com/mingrammer/round
[inkscape]: https://inkscape.org/ko/release

### Update Aliases

Some node classes have alias. For example, `aws.compute.ECS` class is an alias
of `aws.compute.ElasticContainerService` class. Aliases also were auto-generated
from `ALIASES` map in [config.py](config.py).

So, if you want to add new aliases or update existing aliases, you can just add
or update the `ALIASES` map in [config.py](config.py).

Then just run the `./autogen.sh` to generate the added or updated aliases.

> IMPORTANT NOTE: To run `autogen.sh`, you need [round][round] and
> [inkscape][inkscape] command lines that are used for clearning the image
> resource filenames.

## Run Tests

```shell
python -m unittest tests/*.py -v
```
