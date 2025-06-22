#!/bin/sh

# Find the directory containing the glpsol executable.
# The nix store path can be complex, so we search for it.
GLPK_DIR=$(find /nix/store -name glpsol -type f -exec dirname {} \; | head -n 1)

if [ -n "$GLPK_DIR" ]; then
  echo "Found GLPK binary directory: $GLPK_DIR"
  # Add the glpk binary directory to the PATH.
  export PATH="$PATH:$GLPK_DIR"
  echo "Updated PATH: $PATH"
else
  echo "WARNING: glpsol executable not found in /nix/store"
fi

# Start the application
echo "Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:$PORT run:app 