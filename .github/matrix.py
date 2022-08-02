# Copyright 2019 Ilya Shipitsin <chipitsine@gmail.com>
# Copyright 2020 Tim Duesterhus <tim@bastelstu.be>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version
# 2 of the License, or (at your option) any later version.

import json
import sys

if len(sys.argv) == 2:
    build_type = sys.argv[1]
else:
    print(f"Usage: {sys.argv[0]} <build_type>", file=sys.stderr)
    sys.exit(1)

print(f"Generating matrix for type '{build_type}'.")


def clean_os(os):
    if os == "ubuntu-latest":
        return "Ubuntu"
    elif os == "macos-latest":
        return "macOS"
    return os.replace("-latest", "")


def clean_ssl(ssl):
    return ssl.replace("_VERSION", "").lower()


def clean_compression(compression):
    return compression.replace("USE_", "").lower()


def get_asan_flags(cc):
    if cc == "clang":
        return [
            "USE_OBSOLETE_LINKER=1",
            'DEBUG_CFLAGS="-g -fsanitize=address"',
            'LDFLAGS="-fsanitize=address"',
            'CPU_CFLAGS.generic="-O1"',
        ]

    raise ValueError("ASAN is only supported for clang")


matrix = []

# Ubuntu

os = "ubuntu-latest"
TARGET = "linux-glibc"
for CC in ["gcc", "clang"]:
    matrix.extend(
        (
            {
                "name": f"{clean_os(os)}, {CC}, no features",
                "os": os,
                "TARGET": TARGET,
                "CC": CC,
                "FLAGS": [],
            },
            {
                "name": f"{clean_os(os)}, {CC}, all features",
                "os": os,
                "TARGET": TARGET,
                "CC": CC,
                "FLAGS": [
                    "USE_ZLIB=1",
                    "USE_PCRE=1",
                    "USE_PCRE_JIT=1",
                    "USE_LUA=1",
                    "USE_OPENSSL=1",
                    "USE_SYSTEMD=1",
                    "USE_WURFL=1",
                    "WURFL_INC=contrib/wurfl",
                    "WURFL_LIB=contrib/wurfl",
                    "USE_DEVICEATLAS=1",
                    "DEVICEATLAS_SRC=contrib/deviceatlas",
                    "EXTRA_OBJS=contrib/prometheus-exporter/service-prometheus.o",
                    "USE_51DEGREES=1",
                    "51DEGREES_SRC=contrib/51d/src/pattern",
                ],
            },
        )
    )

    matrix.extend(
        {
            "name": f"{clean_os(os)}, {CC}, gz={clean_compression(compression)}",
            "os": os,
            "TARGET": TARGET,
            "CC": CC,
            "FLAGS": [compression],
        }
        for compression in ["USE_SLZ=1", "USE_ZLIB=1"]
    )

    for ssl in [
        "stock",
        "OPENSSL_VERSION=1.0.2u",
        "LIBRESSL_VERSION=2.9.2",
        "LIBRESSL_VERSION=3.3.0",
        "BORINGSSL=yes",
    ]:
        flags = ["USE_OPENSSL=1"]
        if ssl != "stock":
            flags.extend(("SSL_LIB=${HOME}/opt/lib", "SSL_INC=${HOME}/opt/include"))
        matrix.append(
            {
                "name": f"{clean_os(os)}, {CC}, ssl={clean_ssl(ssl)}",
                "os": os,
                "TARGET": TARGET,
                "CC": CC,
                "ssl": ssl,
                "FLAGS": flags,
            }
        )


# ASAN

os = "ubuntu-latest"
CC = "clang"
TARGET = "linux-glibc"
matrix.append(
    {
        "name": f"{clean_os(os)}, {CC}, ASAN, all features",
        "os": os,
        "TARGET": TARGET,
        "CC": CC,
        "FLAGS": get_asan_flags(CC)
        + [
            "USE_ZLIB=1",
            "USE_PCRE=1",
            "USE_PCRE_JIT=1",
            "USE_LUA=1",
            "USE_OPENSSL=1",
            "USE_SYSTEMD=1",
            "USE_WURFL=1",
            "WURFL_INC=contrib/wurfl",
            "WURFL_LIB=contrib/wurfl",
            "USE_DEVICEATLAS=1",
            "DEVICEATLAS_SRC=contrib/deviceatlas",
            "EXTRA_OBJS=contrib/prometheus-exporter/service-prometheus.o",
            "USE_51DEGREES=1",
            "51DEGREES_SRC=contrib/51d/src/pattern",
        ],
    }
)


# macOS

os = "macos-latest"
TARGET = "osx"
matrix.extend(
    {
        "name": f"{clean_os(os)}, {CC}, no features",
        "os": os,
        "TARGET": TARGET,
        "CC": CC,
        "FLAGS": [],
    }
    for CC in ["clang"]
)

# Print matrix

print(json.dumps(matrix, indent=4, sort_keys=True))

print("::set-output name=matrix::{}".format(json.dumps({"include": matrix})))
