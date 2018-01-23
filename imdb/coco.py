from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    import cPickle as pickle
except ImportError:
    import pickle
import os.path
import numpy as np

from nms_net import cfg
from imdb.tools import validate_boxes

from pycocotools.coco import COCO


def load_coco(split, year):
    name = 'coco_{}_{}'.format(year, split)

    cache_file = os.path.join(cfg.ROOT_DIR, 'data', 'cache',
                              '{}.pkl'.format(name))
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as fp:
            return pickle.load(fp)

    ann_file = os.path.join(cfg.ROOT_DIR, 'data', 'coco', 'annotations',
                            'instances_{}{}.json'.format(split, year))
    has_gt = True
    if not os.path.exists(ann_file):
        ann_file = os.path.join(cfg.ROOT_DIR, 'data', 'coco', 'annotations',
                                'image_info_{}{}.json'.format(split, year))
        has_gt = False
    coco = COCO(ann_file)
    categories = coco.loadCats(coco.getCatIds())
    classes = tuple(['__background__'] + [c['name'] for c in categories])
    class_to_ind = {cl: ind for ind, cl in enumerate(classes)}
    class_to_cat_id = {cat['name']: cat['id'] for cat in categories}

    cat_id_to_class_ind = {class_to_cat_id[cls]: class_to_ind[cls]
                           for cls in classes[1:]}

    path_to_images = {
        'coco_2014_train': 'train2014',
        'coco_2014_debug': 'train2014',
        'coco_2014_val': 'val2014',
        'coco_2014_minival': 'val2014',
        'coco_2014_valminusminival': 'val2014',
    }
    roidb = load_im_info(coco, path_to_images[name])
    # gt_splits = {'train', 'val', 'minival', 'minival2'}
    if has_gt:
        print('converting annotations')
        gt_roidb = load_annotations(coco, cat_id_to_class_ind)
        roidb = merge_roidbs(roidb, gt_roidb)

    print('loading detections')
    # TODO(jhosang): shouldn't use cfg.train here, might be reading val or test
    det_roidb = load_detections(coco, name, cfg.train.detector, cat_id_to_class_ind)
    roidb = merge_roidbs(roidb, det_roidb)

    imdb = {
        'name': name,
        'classes': classes,
        'class_to_ind': class_to_ind,
        'class_to_cat_id': class_to_cat_id,
        'num_classes': len(classes) - 1,
        'roidb': roidb,
    }
    return imdb


def load_detections(coco, imdb_name, detector, cat_id_to_class_ind):
    filename = os.path.join(cfg.ROOT_DIR, 'data',
                            '{}_{}.pkl'.format(imdb_name, detector))
    with open(filename, 'rb') as fp:
        dets, det_im_ids, cat_ids = pickle.load(fp, encoding='latin1')

    roidb = []
    for i, imid in enumerate(det_im_ids):
        cls = []
        imdets = []
        scores = []
        for cat_i, cat_id in enumerate(cat_ids):
            t_dets = dets[cat_i][i]
            if (isinstance(t_dets, list) and len(t_dets) == 0) or t_dets.size == 0:
                continue
            n = t_dets.shape[0]
            cls_ind = cat_id_to_class_ind[cat_id]
            cls.append(np.zeros((n,), dtype=np.int32) + cls_ind)
            imdets.append(t_dets[:, :4])
            scores.append(t_dets[:, 4])
        if not cls:
            continue
        cls = np.concatenate(cls, axis=0)
        scores = np.concatenate(scores, axis=0)
        imdets = np.concatenate(imdets, axis=0)

        # drop too small detections
        w = imdets[:, 2] - imdets[:, 0]
        h = imdets[:, 3] - imdets[:, 1]
        min_size = cfg.train.det_min_size
        valid = np.logical_and(w >= min_size, h >= min_size)
        cls = cls[valid]
        scores = scores[valid]
        imdets = imdets[valid, :]

        im_info = coco.loadImgs(imid)[0]
        width = im_info['width']
        height = im_info['height']
        validate_boxes(imdets, width=width, height=height)

        roidb.append({
            'id': imid,
            'dets': imdets,
            'det_scores': scores,
            'det_classes': cls,
        })
    return roidb


def merge_roidbs(roidb_a, roidb_b):
    assert len(roidb_a) >= len(roidb_b)
    imid_to_roidb_a = {r['id']: r for r in roidb_a}
    for roi_b in roidb_b:
        imid = roi_b['id']
        roi_a = imid_to_roidb_a[imid]
        roi_a.update(roi_b)
    return roidb_a


def load_im_info(coco, path_to_images):
    image_ids = coco.getImgIds()
    roidb = []
    for image_id in image_ids:
        im_info = coco.loadImgs(image_id)[0]
        filename = os.path.join(cfg.ROOT_DIR, 'data', 'coco', 'images',
                                path_to_images, im_info['file_name'])
        roidb.append({
            'id': im_info['id'],
            'width': im_info['width'],
            'height': im_info['height'],
            'filename': filename,
            'flipped': False,
        })
    return roidb


def load_annotations(coco, cat_id_to_class_ind):
    image_ids = coco.getImgIds()
    gt_roidb = [load_image_annos(coco, image_id, cat_id_to_class_ind)
                for image_id in image_ids]
    return gt_roidb


def load_image_annos(coco, image_id, cat_id_to_class_ind):
    im_info = coco.loadImgs(image_id)[0]
    width = im_info['width']
    height = im_info['height']
    ann_ids = coco.getAnnIds(imgIds=image_id)
    objs = coco.loadAnns(ann_ids)
    objs = sanitize_anno_bboxes(objs, width, height)
    num_objs = len(objs)

    boxes = np.zeros((num_objs, 4), dtype=np.float32)
    classes = np.zeros((num_objs), dtype=np.int32)
    crowd = np.zeros((num_objs), dtype=np.bool)
    for i, obj in enumerate(objs):
        boxes[i, :] = obj['clean_bbox']
        crowd[i] = obj['iscrowd']
        cls = cat_id_to_class_ind[obj['category_id']]
        classes[i] = cls

    w = boxes[:, 2] - boxes[:, 0]
    h = boxes[:, 3] - boxes[:, 1]
    min_size = cfg.train.det_min_size
    valid = np.logical_and(w >= min_size, h >= min_size)
    classes = classes[valid]
    crowd = crowd[valid]
    boxes = boxes[valid, :]

    validate_boxes(boxes, width=width, height=height)
    return {
        'id': im_info['id'],
        'gt_boxes': boxes,
        'gt_classes': classes,
        'gt_crowd': crowd,
    }


def sanitize_anno_bboxes(objs, width, height):
    valid_objs = []
    for obj in objs:
        x1 = max(0, obj['bbox'][0])
        y1 = max(0, obj['bbox'][1])
        x2 = min(width, x1 + max(0, obj['bbox'][2]))
        y2 = min(height, y1 + max(0, obj['bbox'][3]))
        if obj['area'] > 0 and x2 >= x1 and y2 >= y1:
            obj['clean_bbox'] = [x1, y1, x2, y2]
            valid_objs.append(obj)
    return valid_objs


if __name__ == '__main__':
    imdb = load_coco('minival', '2014')
