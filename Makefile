
TF_INC="/home/yoon28/devtools/anaconda3/lib/python3.5/site-packages/tensorflow/include"
YOON_INC="/home/yoon28/devtools/anaconda3/lib/python3.5/site-packages/tensorflow/include/external/nsync/public"
TF_LIB="/home/yoon28/devtools/anaconda3/lib/python3.5/site-packages/tensorflow"

.PHONY: all

all: nms_net/matching_module/det_matching.so nms_net/roi_pooling_layer/roi_pooling.so imdb/file_formats/AnnoList_pb2.py

nms_net/roi_pooling_layer/roi_pooling.so: nms_net/roi_pooling_layer/roi_pooling_op.o nms_net/roi_pooling_layer/roi_pooling_op_gpu.o
	g++ -std=c++11 -shared $^ -o $@ -fPIC -I ${TF_INC} -I ${YOON_INC} -L${TF_LIB} -ltensorflow_framework -O2 -D_GLIBCXX_USE_CXX11_ABI=0

%.o: %.cc
	g++ -std=c++11 -c $< -o $@ -fPIC -I ${TF_INC} -I ${YOON_INC} -L${TF_LIB} -ltensorflow_framework -O2 -D_GLIBCXX_USE_CXX11_ABI=0 

%.o: %.cu
	nvcc -std=c++11 -c $< -o $@ -I ${TF_INC} -I ${YOON_INC} -O2 -x cu -arch=sm_61 -D GOOGLE_CUDA=1 -Xcompiler -fPIC -D_GLIBCXX_USE_CXX11_ABI=0 

%.so: %.cc
	g++ -std=c++11 -shared $< -o $@ -fPIC -I ${TF_INC} -I ${YOON_INC} -L${TF_LIB} -ltensorflow_framework -O2 -D_GLIBCXX_USE_CXX11_ABI=0

%_pb2.py: %.proto
	protoc --python_out=. $<

clean:
	rm nms_net/roi_pooling_layer/*.so
	rm nms_net/roi_pooling_layer/*.o
	rm nms_net/matching_module/*.so
	rm imdb/file_formats/AnnoList_pb2.py
