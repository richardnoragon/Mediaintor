# M19 native Linux desktop container

This package opens native Wayland windows. It does not provide a web server.
The image includes Calibre, Poppler, FFmpeg and mpv. Containers run as your user,
without runtime networking, with a read-only image and persistent application
state. Source documents are accessed only through explicitly configured mounts.

Build an application archive with `python3 tools/build_package.py --output dist`.
Copy the archive into a build directory as `candidate.tar.gz`, alongside
Dockerfile and entrypoint.py from this directory. Build with:

    docker build --build-arg PACKAGE_SHA256=<archive-sha256> -t mediainator:m19 <build-directory>

Run the image as your numeric UID:GID. Mount a persistent writable directory at
`/home/mediainator`, and your active Wayland socket at `/tmp/runtime/wayland-0`.
Provide a private writable `/tmp/runtime` owned by that UID and a writable `/tmp`.
Run the `install` command once before `run`; installation is explicit and retains
user data. Never mount the Docker socket or the entire host home directory.

External readers and players run inside the container. Music/movie playback can
use `mpv {playlist}` in player settings. Audible playback additionally requires
the session PulseAudio-compatible socket (PipeWire supports this); mount only
that socket and set PULSE_SERVER to its container path. Host desktop applications
are not automatically available inside the container.

Keep M16 and M19 state directories separate. Close the application normally
before copying its state. Rollback uses the retained M16 installation, not a
schema downgrade of an M19 library. A container image backup is not a data backup.

## Install the exported image on this Linux machine

    docker load --input dist/mediainator-m19-docker.tar

For a fresh installation, create `active/home`, `active/library`, and
`active/import-sources` under a chosen deployment directory. Then:

    python3 packaging/docker/control.py install --root /absolute/deployment/directory
    python3 packaging/docker/control.py verify --root /absolute/deployment/directory
    python3 packaging/docker/control.py run --root /absolute/deployment/directory --detach

The host needs Docker access and an active Wayland session. The default image
name is `mediainator:m19`; `--image sha256:...` pins a particular image. The app
container is named `mediainator-m19-everyday`. Close its window normally before
relaunching or upgrading. An already running instance prevents a second launch.
Import files are available inside the app at `/data/import-sources`; copy files
into the deployment's `active/import-sources` to make them available. The Calibre
library is mounted at `/data/library`. Do not open the same library concurrently
in another app. Newly selected host paths outside these mounts are unavailable.

For existing users, copy the stopped deployment's entire `active` directory,
preserving symlinks, into a new deployment directory before the install step.
Do not copy acceptance profiles. Keep the prior deployment for rollback.
