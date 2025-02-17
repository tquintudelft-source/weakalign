# from __future__ import print_function, division
# import os
# import argparse
# from os.path import exists
# from torch.utils.data import DataLoader
# from model.cnn_geometric_model import TwoStageCNNGeometric
# from data.gpe_dataset import GPEDataset
# from data.pf_dataset import PFDataset
# # from data import download_PF_pascal
# from image.normalization import NormalizeImageDict, normalize_image
# from util.torch_util import BatchTensorToVars
# from geotnf.transformation import GeometricTnf
# from geotnf.point_tnf import PointsToUnitCoords
# from data import *
# import matplotlib.pyplot as plt
# from skimage import io
# from collections import OrderedDict
# import torch.nn.functional as F
# import torch
#
# if __name__ == '__main__':
#
#     # for compatibility with Python 2
#     try:
#         input = raw_input
#     except NameError:
#         pass
#
#     """
#
#     Script to demonstrate evaluation on a trained model
#
#     """
#
#     print('WeakAlign demo script')
#
#     # Argument parsing
#     parser = argparse.ArgumentParser(description='WeakAlign PyTorch implementation')
#     # Paths
#     parser.add_argument('--model', type=str, default='trained_models/weakalign_resnet101_affine_tps.pth.tar', help='Trained two-stage model filename')
#     parser.add_argument('--model-aff', type=str, default='', help='Trained affine model filename')
#     parser.add_argument('--model-tps', type=str, default='', help='Trained TPS model filename')
#     parser.add_argument('--gpe-path', type=str, default='datasets/proposal-flow-pascal/', help='Path to PF dataset')
#     parser.add_argument('--feature-extraction-cnn', type=str, default='resnet101', help='feature extraction CNN model architecture: vgg/resnet101')
#     parser.add_argument('--tps-reg-factor', type=float, default=0.0, help='regularisation factor for tps tnf')
#
#     args = parser.parse_args()
#
#     use_cuda = torch.cuda.is_available()
#
#     do_aff = not args.model_aff==''
#     do_tps = not args.model_tps==''
#
#     if args.gpe_path=='':
#         args.args.gpe_path='datasets/proposal-flow-pascal/'
#
#     # Download dataset if needed
#     # if not exists(args.pf_path):
#     #     download_PF_pascal(args.pf_path)
#
#     # Create model
#     print('Creating CNN model...')
#     model = TwoStageCNNGeometric(use_cuda=use_cuda,
#                                  return_correlation=False,
#                                  feature_extraction_cnn=args.feature_extraction_cnn)
#
#     # Load trained weights
#     print('Loading trained model weights...')
#     if args.model!='':
#         checkpoint = torch.load(args.model, map_location=lambda storage, loc: storage)
#         checkpoint['state_dict'] = OrderedDict([(k.replace('vgg', 'model'), v) for k, v in checkpoint['state_dict'].items()])
#
#         feature_extraction_dict = {k: v for k, v in model.FeatureExtraction.state_dict().items() if
#                                    'num_batches_tracked' not in k}
#         for name, param in feature_extraction_dict.items():
#             model.FeatureExtraction.state_dict()[name].copy_(checkpoint['state_dict']['FeatureExtraction.' + name])
#
#         feature_reg_dict = {k: v for k, v in model.FeatureRegression.state_dict().items() if
#                             'num_batches_tracked' not in k}
#         for name, param in feature_reg_dict.items():
#             model.FeatureRegression.state_dict()[name].copy_(checkpoint['state_dict']['FeatureRegression.' + name])
#
#         feature_reg2_dict = {k: v for k, v in model.FeatureRegression2.state_dict().items() if
#                              'num_batches_tracked' not in k}
#         for name, param in feature_reg2_dict.items():
#             model.FeatureRegression2.state_dict()[name].copy_(
#                 checkpoint['state_dict']['FeatureRegression2.' + name])
#
#
#         # for name, param in model.FeatureExtraction.state_dict().items():
#         #     model.FeatureExtraction.state_dict()[name].copy_(checkpoint['state_dict']['FeatureExtraction.' + name])
#         # for name, param in model.FeatureRegression.state_dict().items():
#         #     model.FeatureRegression.state_dict()[name].copy_(checkpoint['state_dict']['FeatureRegression.' + name])
#         # for name, param in model.FeatureRegression2.state_dict().items():
#         #     model.FeatureRegression2.state_dict()[name].copy_(checkpoint['state_dict']['FeatureRegression2.' + name])
#
#     else:
#         checkpoint_aff = torch.load(args.model_aff, map_location=lambda storage, loc: storage)
#         checkpoint_aff['state_dict'] = OrderedDict([(k.replace('vgg', 'model'), v) for k, v in checkpoint_aff['state_dict'].items()])
#         for name, param in model.FeatureExtraction.state_dict().items():
#             model.FeatureExtraction.state_dict()[name].copy_(checkpoint_aff['state_dict']['FeatureExtraction.' + name])
#         for name, param in model.FeatureRegression.state_dict().items():
#             model.FeatureRegression.state_dict()[name].copy_(checkpoint_aff['state_dict']['FeatureRegression.' + name])
#
#         checkpoint_tps = torch.load(args.model_tps, map_location=lambda storage, loc: storage)
#         checkpoint_tps['state_dict'] = OrderedDict([(k.replace('vgg', 'model'), v) for k, v in checkpoint_tps['state_dict'].items()])
#         for name, param in model.FeatureRegression2.state_dict().items():
#             model.FeatureRegression2.state_dict()[name].copy_(checkpoint_tps['state_dict']['FeatureRegression.' + name])
#
#
#     # Dataset and dataloader
#     # dataset = ******(csv_file=os.path.join(args.pf_path, 'test_pairs_pf_pascal.csv'),
#     #                     dataset_path=args.pf_path,
#     #                     transform=NormalizeImageDict(['source_image','target_image']))
#
#     dataset = PFDataset(csv_file=os.path.join(args.gpe_path, 'test_pairs_pf_pascal.csv'),
#                         dataset_path=args.gpe_path,
#                         transform=NormalizeImageDict(['source_image','target_image']))
#
#     dataloader = DataLoader(dataset, batch_size=1,
#                             shuffle=True, num_workers=4)
#
#     batchTensorToVars = BatchTensorToVars(use_cuda=use_cuda)
#
#
#     # Instatiate image transformers
#     affTnf = GeometricTnf(geometric_model='affine', use_cuda=use_cuda)
#     def affTpsTnf(source_image, theta_aff, theta_aff_tps, use_cuda=use_cuda):
#         tpstnf = GeometricTnf(geometric_model = 'tps',use_cuda=use_cuda)
#         sampling_grid = tpstnf(image_batch=source_image,
#                                theta_batch=theta_aff_tps,
#                                return_sampling_grid=True)[1]
#         X = sampling_grid[:,:,:,0].unsqueeze(3)
#         Y = sampling_grid[:,:,:,1].unsqueeze(3)
#         Xp = X*theta_aff[:,0].unsqueeze(1).unsqueeze(2)+Y*theta_aff[:,1].unsqueeze(1).unsqueeze(2)+theta_aff[:,2].unsqueeze(1).unsqueeze(2)
#         Yp = X*theta_aff[:,3].unsqueeze(1).unsqueeze(2)+Y*theta_aff[:,4].unsqueeze(1).unsqueeze(2)+theta_aff[:,5].unsqueeze(1).unsqueeze(2)
#         sg = torch.cat((Xp,Yp),3)
#         warped_image_batch = F.grid_sample(source_image, sg)
#
#         return warped_image_batch
#
#
#     for i, batch in enumerate(dataloader):
#         # get random batch of size 1
#         batch = batchTensorToVars(batch)
#
#         source_im_size = batch['source_im_size']
#         target_im_size = batch['target_im_size']
#
#         source_points = batch['source_points']
#         target_points = batch['target_points']
#
#         # warp points with estimated transformations
#         target_points_norm = PointsToUnitCoords(target_points,target_im_size)
#
#         model.eval()
#
#         # Evaluate model
#         theta_aff,theta_aff_tps=model(batch)
#
#         warped_image_aff = affTnf(batch['source_image'],theta_aff.view(-1,2,3))
#         warped_image_aff_tps = affTpsTnf(batch['source_image'],theta_aff, theta_aff_tps)
#
#
#         # Un-normalize images and convert to numpy
#         source_image = normalize_image(batch['source_image'],forward=False)
#         source_image = source_image.data.squeeze(0).transpose(0,1).transpose(1,2).cpu().numpy()
#         target_image = normalize_image(batch['target_image'],forward=False)
#         target_image = target_image.data.squeeze(0).transpose(0,1).transpose(1,2).cpu().numpy()
#
#         warped_image_aff = normalize_image(warped_image_aff,forward=False)
#         warped_image_aff = warped_image_aff.data.squeeze(0).transpose(0,1).transpose(1,2).cpu().numpy()
#
#         warped_image_aff_tps = normalize_image(warped_image_aff_tps,forward=False)
#         warped_image_aff_tps = warped_image_aff_tps.data.squeeze(0).transpose(0,1).transpose(1,2).cpu().numpy()
#
#         # check if display is available
#         exit_val = os.system('python -c "import matplotlib.pyplot as plt;plt.figure()"  > /dev/null 2>&1')
#         display_avail = exit_val==0
#
#         if True:
#             N_subplots = 4
#             fig, axs = plt.subplots(1,N_subplots)
#             axs[0].imshow(source_image)
#             axs[0].set_title('source')
#             axs[1].imshow(target_image)
#             axs[1].set_title('target')
#             axs[2].imshow(warped_image_aff)
#             axs[2].set_title('affine')
#             axs[3].imshow(warped_image_aff_tps)
#             axs[3].set_title('affine+RAS')
#
#             for k in range(N_subplots):
#                 axs[k].axis('off')
#             print('Showing results. Close figure window to continue')
#             plt.show()
#
#             print('Writing results to:')
#             fn_src = 'source'+str(i)+'.png'
#             print(fn_src)
#             io.imsave(fn_src, source_image)
#             fn_tgt = 'target'+str(i)+'.png'
#             print(fn_tgt)
#             io.imsave(fn_tgt, target_image)
#             fn_aff = 'result_aff'+str(i)+'.png'
#             print(fn_aff)
#             io.imsave(fn_aff, warped_image_aff)
#             fn_aff_tps = 'result_aff_tps'+str(i)+'.png'
#             print(fn_aff_tps)
#             io.imsave(fn_aff_tps,warped_image_aff_tps)
#
#         res = input('Run for another example ([y]/n): ')
#         if res=='n':
#             break
#
from __future__ import print_function, division
import os
import argparse
import torch
import torch.nn as nn
from os.path import exists
from torch.utils.data import Dataset, DataLoader
from model.cnn_geometric_model import CNNGeometric, TwoStageCNNGeometric
from data.pf_dataset import PFDataset, PFPascalDataset
from data.download_datasets import download_PF_willow
from image.normalization import NormalizeImageDict, normalize_image
from util.torch_util import BatchTensorToVars, str_to_bool
from geotnf.transformation import GeometricTnf
from geotnf.point_tnf import *
import matplotlib.pyplot as plt
from skimage import io
from collections import OrderedDict
import torch.nn.functional as F
import shutil

if __name__ == '__main__':

    def clean(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    # for compatibility with Python 2
    try:
        input = raw_input
    except NameError:
        pass

    """
    Script to demonstrate evaluation on a trained model
    """

    print('WeakAlign demo script')

    # Argument parsing
    parser = argparse.ArgumentParser(description='WeakAlign PyTorch implementation')
    # Paths
    parser.add_argument('--model', type=str, default='trained_models/weakalign_resnet101_affine_tps.pth.tar',
                        help='Trained two-stage model filename')
    parser.add_argument('--model-aff', type=str, default='', help='Trained affine model filename')
    parser.add_argument('--model-tps', type=str, default='', help='Trained TPS model filename')
    parser.add_argument('--pf-path', type=str, default='datasets/proposal-flow-pascal', help='Path to PF dataset')
    parser.add_argument('--feature-extraction-cnn', type=str, default='vgg',
                        help='feature extraction CNN model architecture: vgg/resnet101')
    parser.add_argument('--tps-reg-factor', type=float, default=0.0, help='regularisation factor for tps tnf')

    args = parser.parse_args()

    use_cuda = torch.cuda.is_available()

    do_aff = not args.model_aff == ''
    do_tps = not args.model_tps == ''

    if args.pf_path == '':
        args.args.pf_path = 'datasets/proposal-flow-pascal/'

    # Download dataset if needed
    if not exists(args.pf_path):
        download_PF_pascal(args.pf_path)

    # Create model
    print('Creating CNN model...')


    # do_aff_only = False
    # do_tps_only = False
    #
    # if do_aff_only:
    #     model = CNNGeometric(use_cuda=use_cuda,
    #                              output_dim=18,
    #                              **arg_groups['model'])

    model = TwoStageCNNGeometric(use_cuda=use_cuda,
                                 return_correlation=False,
                                 feature_extraction_cnn=args.feature_extraction_cnn)

    # Load trained weights
    print('Loading trained model weights...')
    if args.model != '':
        print(args.model)
        checkpoint = torch.load(args.model, map_location=lambda storage, loc: storage)
        checkpoint['state_dict'] = OrderedDict([(k.replace('vgg', 'model'), v) for k, v in checkpoint['state_dict'].items()])

        feature_extraction_dict = {k: v for k, v in model.FeatureExtraction.state_dict().items() if
                                   'num_batches_tracked' not in k}
        for name, param in feature_extraction_dict.items():
            model.FeatureExtraction.state_dict()[name].copy_(checkpoint['state_dict']['FeatureExtraction.' + name])

        feature_reg_dict = {k: v for k, v in model.FeatureRegression.state_dict().items() if
                            'num_batches_tracked' not in k}
        for name, param in feature_reg_dict.items():
            model.FeatureRegression.state_dict()[name].copy_(checkpoint['state_dict']['FeatureRegression.' + name])

        feature_reg2_dict = {k: v for k, v in model.FeatureRegression2.state_dict().items() if
                             'num_batches_tracked' not in k}
        for name, param in feature_reg2_dict.items():
            model.FeatureRegression2.state_dict()[name].copy_(
                checkpoint['state_dict']['FeatureRegression2.' + name])

    else:
        checkpoint_aff = torch.load(args.model_aff, map_location=lambda storage, loc: storage)
        checkpoint_aff['state_dict'] = OrderedDict(
            [(k.replace('vgg', 'model'), v) for k, v in checkpoint_aff['state_dict'].items()])
        for name, param in model.FeatureExtraction.state_dict().items():
            model.FeatureExtraction.state_dict()[name].copy_(checkpoint_aff['state_dict']['FeatureExtraction.' + name])
        for name, param in model.FeatureRegression.state_dict().items():
            model.FeatureRegression.state_dict()[name].copy_(checkpoint_aff['state_dict']['FeatureRegression.' + name])

        checkpoint_tps = torch.load(args.model_tps, map_location=lambda storage, loc: storage)
        checkpoint_tps['state_dict'] = OrderedDict(
            [(k.replace('vgg', 'model'), v) for k, v in checkpoint_tps['state_dict'].items()])
        for name, param in model.FeatureRegression2.state_dict().items():
            model.FeatureRegression2.state_dict()[name].copy_(checkpoint_tps['state_dict']['FeatureRegression.' + name])

    # Dataset and dataloader
    dataset = PFPascalDataset(csv_file=os.path.join(args.pf_path, 'test_pairs_nw.csv'),
                              dataset_path=args.pf_path,
                              transform=NormalizeImageDict(['source_image', 'target_image']))
    dataloader = DataLoader(dataset, batch_size=1,
                            shuffle=True, num_workers=4)
    batchTensorToVars = BatchTensorToVars(use_cuda=use_cuda)

    # Instatiate image transformers
    affTnf = GeometricTnf(geometric_model='affine', use_cuda=use_cuda)


    def affTpsTnf(source_image, theta_aff, theta_aff_tps, use_cuda=use_cuda):
        tpstnf = GeometricTnf(geometric_model='tps', use_cuda=use_cuda)
        sampling_grid = tpstnf(image_batch=source_image,
                               theta_batch=theta_aff_tps,
                               return_sampling_grid=True)[1]
        X = sampling_grid[:, :, :, 0].unsqueeze(3)
        Y = sampling_grid[:, :, :, 1].unsqueeze(3)
        Xp = X * theta_aff[:, 0].unsqueeze(1).unsqueeze(2) + Y * theta_aff[:, 1].unsqueeze(1).unsqueeze(2) + theta_aff[:,
                                                                                                             2].unsqueeze(
            1).unsqueeze(2)
        Yp = X * theta_aff[:, 3].unsqueeze(1).unsqueeze(2) + Y * theta_aff[:, 4].unsqueeze(1).unsqueeze(2) + theta_aff[:,
                                                                                                             5].unsqueeze(
            1).unsqueeze(2)
        sg = torch.cat((Xp, Yp), 3)
        warped_image_batch = F.grid_sample(source_image, sg)

        return warped_image_batch


    source_num = 0

    clean('out/')

    for i, batch in enumerate(dataloader):
        # get random batch of size 1
        batch = batchTensorToVars(batch)

        source_im_size = batch['source_im_size']
        target_im_size = batch['target_im_size']

        source_points = batch['source_points']
        target_points = batch['target_points']

        # warp points with estimated transformations
        target_points_norm = PointsToUnitCoords(target_points, target_im_size)

        model.eval()

        # Evaluate model
        theta_aff, theta_aff_tps = model(batch)

        warped_image_aff = affTnf(batch['source_image'], theta_aff.view(-1, 2, 3))
        warped_image_aff_tps = affTpsTnf(batch['source_image'], theta_aff, theta_aff_tps)

        # Un-normalize images and convert to numpy
        source_image = normalize_image(batch['source_image'], forward=False)
        source_image = source_image.data.squeeze(0).transpose(0, 1).transpose(1, 2).cpu().numpy()
        target_image = normalize_image(batch['target_image'], forward=False)
        target_image = target_image.data.squeeze(0).transpose(0, 1).transpose(1, 2).cpu().numpy()

        warped_image_aff = normalize_image(warped_image_aff, forward=False)
        warped_image_aff = warped_image_aff.data.squeeze(0).transpose(0, 1).transpose(1, 2).cpu().numpy()

        warped_image_aff_tps = normalize_image(warped_image_aff_tps, forward=False)
        warped_image_aff_tps = warped_image_aff_tps.data.squeeze(0).transpose(0, 1).transpose(1, 2).cpu().numpy()

        # check if display is available
        exit_val = os.system('python -c "import matplotlib.pyplot as plt;plt.figure()"  > /dev/null 2>&1')
        display_avail = exit_val == 0

        if True:
            N_subplots = 3
            fig, axs = plt.subplots(1, N_subplots)
            axs[0].imshow(source_image)
            axs[0].set_title('source')
            axs[1].imshow(target_image)
            axs[1].set_title('target')
            axs[2].imshow(warped_image_aff)
            axs[2].set_title('affine')
            # axs[3].imshow(warped_image_aff_tps)
            # axs[3].set_title('affine + thin plate spline')

            for i in range(N_subplots):
                axs[i].axis('off')

            manager = plt.get_current_fig_manager()
            manager.full_screen_toggle()
            print('Showing results. Close figure window to continue')
            plt.show()

            # fn_src = 'out/source'+str(source_num)+'.png'
            # print(fn_src)
            # io.imsave(fn_src, source_image)

            # fn_tgt = 'out/target'+str(source_num)+'.png'
            # print(fn_tgt)
            # io.imsave(fn_tgt, target_image)

            fn_aff = 'out/result_resnet_aff'+str(source_num)+'.png'
            print(fn_aff)
            io.imsave(fn_aff, warped_image_aff)

            # fn_aff_tps = 'result_aff_tps'+str(source_num)+'.png'
            # print(fn_aff_tps)
            # io.imsave(fn_aff_tps, warped_image_aff_tps)

            source_num += 1


        # res = input('Run for another example ([y]/n): ')
        # if res == 'n':
        #     break

