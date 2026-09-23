#!/usr/bin/env bash
set -euo pipefail
export PATH="/mingw64/bin:/usr/bin:$PATH"
temple_here="$(cd "$(dirname "$0")" && pwd)"
temple_root="$(cd "$temple_here/../local/encoder" && pwd)"
temple_prefix="$temple_root/prefix"
mkdir -p "$temple_prefix/include" "$temple_prefix/lib" "$temple_root/output"
gcc --version > "$temple_root/output/toolchain.txt"
make --version >> "$temple_root/output/toolchain.txt"
cd "$temple_root/zlib-1.3.1"
make -f win32/Makefile.gcc -j8 libz.a
cp libz.a "$temple_prefix/lib/"
cp zlib.h zconf.h "$temple_prefix/include/"
cd "$temple_root/x264"
./configure --host=x86_64-w64-mingw32 --prefix="$temple_prefix" --enable-static --disable-cli --disable-asm --disable-opencl --disable-avs --disable-swscale --disable-lavf --disable-ffms --disable-gpac --disable-lsmash --bit-depth=8 --chroma-format=420 --extra-ldflags=-static
make -j8
make install-lib-static
export PKG_CONFIG_LIBDIR="$temple_prefix/lib/pkgconfig"
export PKG_CONFIG_PATH="$temple_prefix/lib/pkgconfig"
cd "$temple_root/ffmpeg-7.1"
./configure --prefix="$temple_prefix" --target-os=mingw32 --arch=x86_64 --cc=gcc --disable-autodetect --disable-everything --disable-network --disable-doc --disable-debug --disable-ffplay --disable-ffprobe --disable-x86asm --disable-pthreads --enable-w32threads --enable-static --disable-shared --enable-ffmpeg --enable-gpl --enable-libx264 --enable-zlib --enable-protocol=file,pipe --enable-demuxer=image2,image2pipe,mov --enable-decoder=png,h264 --enable-encoder=png,gif,libx264 --enable-muxer=gif,mp4,image2 --enable-parser=h264 --enable-filter=scale,format,pad,split,palettegen,paletteuse,fps,buffer,buffersink,null --extra-cflags="-I$temple_prefix/include" --extra-ldflags="-L$temple_prefix/lib -static" --pkg-config-flags=--static
make -j8
cp ffmpeg.exe "$temple_root/output/compositor-encoder.exe"
./ffmpeg.exe -version > "$temple_root/output/version.txt"
objdump -p ffmpeg.exe | sed -n '/DLL Name:/p' > "$temple_root/output/imports.txt"
