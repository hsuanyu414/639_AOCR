import os
import pandas as pd
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, default=None, help='action to do')
    parser.add_argument('--csv_name', type=str, default='id2serial.csv', help='csv file path')
    parser.add_argument('--dir_folder', type=str, default='Data', help='directory path')
    args = parser.parse_args()
    return args

class Translator:
    def __init__(self, dir_path=None):
        self.pdObject = None
        self.csv_path = os.path.join(os.getcwd(), 'id2serial.csv')
        self.dir_path = os.path.join(os.getcwd(), dir_path)
    def read_csv(self, csv_path):
        self.pdObject = pd.read_csv(csv_path)
    def to_serial(self):
        files = os.listdir(self.dir_path)
        unique_filename = set()
        for filename in files:
            if filename.endswith('_label.nii.gz'):
                unique_filename.add(filename[:-13])
            elif filename.endswith('.nii.gz'):
                unique_filename.add(filename[:-7])
        unique_filename = list(unique_filename)
        unique_filename.sort()
        serial_numbers = list(range(1, len(unique_filename)+1))
        unique_id_serial = pd.DataFrame({'id':unique_filename, 'serial':serial_numbers})
        unique_id_serial.to_csv(self.csv_path, index=False)
        
        
        for filename in files:
            print(filename)
            if filename.endswith('_label.nii.gz'):
                id = filename[:-13]
                os.rename(os.path.join(self.dir_path, filename), os.path.join(self.dir_path, str(unique_id_serial[unique_id_serial['id']==id]['serial'].values[0])+'_label.nii.gz'))
            elif filename.endswith('.nii.gz'):
                id = filename[:-7]
                os.rename(os.path.join(self.dir_path, filename), os.path.join(self.dir_path, str(unique_id_serial[unique_id_serial['id']==id]['serial'].values[0])+'.nii.gz'))
            else:
                continue
    def to_id(self, csv_path):
        self.read_csv(csv_path)
        print(self.pdObject)
        files = os.listdir(self.dir_path)
        for filename in files:
            print(filename)
            if filename.endswith('_label.nii.gz'):
                serial = filename[:-13]
                os.rename(os.path.join(self.dir_path, filename), os.path.join(self.dir_path, str(self.pdObject[self.pdObject['serial']==int(serial)]['id'].values[0])+'_label.nii.gz'))
            elif filename.endswith('.nii.gz'):
                serial = filename[:-7]
                os.rename(os.path.join(self.dir_path, filename), os.path.join(self.dir_path, str(self.pdObject[self.pdObject['serial']==int(serial)]['id'].values[0])+'.nii.gz'))
            else:
                continue

if __name__ == '__main__':
    args = parse_args()
    translator = Translator(dir_path=args.dir_folder)
    print(args)
    if args.action == 'to_serial':
        translator.to_serial()
    elif args.action == 'to_id':
        csv_path = args.csv_name
        translator.to_id(csv_path)
    else:
        print('Please specify the action to do: to_serial or to_id')


            



