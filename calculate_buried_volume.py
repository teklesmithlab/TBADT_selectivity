import pandas as pd
import numpy as np
import dbstep.Dbstep as db

def get_buried_volume(local_xyz_file_dir, atom_no, radius=3.5):
    """
    calculates the buried volume at an atom for the specified radius
    :param local_xyz_file_dir: directory to the xyz file (local)
    :param atom_no: atom index to calculate buried volume at
    :param radius: radius of the cone angle
    :return: percent buried volume, buried shell volume
    """

    # Create DBSTEP object
    mol = db.dbstep(local_xyz_file_dir, atom1=atom_no, r=radius, vshell=0.5)

    # extract volume data
    percent_buried_volume = mol.bur_vol
    buried_shell = mol.bur_shell

    return percent_buried_volume, buried_shell

if __name__ == '__main__':

    # Example usage: analyze buried volume for atoms at various radii
    atom_indices = [1, 2, 3, 4]  # atom indices
    radii = np.arange(1.5, 4.4, 0.1) # radii to test

    # Initialize a dictionary to collect data
    data = {radius: [] for radius in radii}

    for i in range(len(atom_indices)):
        print(f"Processing H atom index: {atom_indices[i]}")
        for radius in radii:
            vbur, shellbur = get_buried_volume('xyz_files/p2_11.xyz', atom_indices[i], radius=radius)
            data[radius].append(vbur)

    # Create DataFrame where rows are hydrogens and columns are radii
    df = pd.DataFrame(data, index=atom_indices)
    df.index.name = 'Atom Index'

    df.to_csv('data/buried_volumes.csv')
