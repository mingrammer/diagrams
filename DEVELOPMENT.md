# Development Guide

## Podman local development setup

You should have podman installed in your system, if not click [here](https://podman.io/).

1. Go to diagrams root directory.

2. Build the docker image.

    ```shell
    podman build --tag diagrams:1.0 -f ./docker/dev/Dockerfile .
    ```

3. Create the container, run in background and mount the project source code.

    ```shell
    podman run -d \
    -it \
    --name diagrams \
    --mount type=bind,source="$(pwd)",target=/usr/src/diagrams \
    diagrams:1.0
    ```

4. Run unit tests in the host using the container to confirm that it's working.

    ```shell
    podman exec diagrams python -m unittest tests/*.py -v
    ```

5. Run the bash script `autogen.sh` to test.

    ```shell
    podman exec diagrams ./autogen.sh
    ```

6. If the unit tests and the bash script `autogen.sh` is working correctly, then your system is now ready for development.

## Podman local development

Say you develop the architecture under `diagram.py` file. To generate picture, run Python interpreter against the code.

   ```shell
   podman exec diagrams python diagram.py
   ```
