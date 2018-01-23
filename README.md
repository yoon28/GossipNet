## Disclaimer

This repository has been cloned from https://github.com/hosang/gossipnet.
All the codes in here are same as original except that tensorflow is modified to fit TF vsersion 1.0.

# Learning non-maximum suppression for object detection
## Paper

This is the code for the paper  
_Learning non-maximum suppression. Jan Hosang, Rodrigo Benenson, Bernt Schiele. CVPR 2017._

You can find the project page with downloads here: https://mpi-inf.mpg.de/learning-nms

## Setup

Run `make` to compile C++ code and protobufs.

Link to the coco API in the root directory, like so:
```
/work/src/tf-gnet$ ln -s /work/src/coco/PythonAPI/pycocotools
```

Link to coco annotations/images in the data subdir:
```
/work/src/tf-gnet/data$ ln -s /datasets/coco
```

