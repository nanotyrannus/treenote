import yaml
import io
from os.path import abspath

def read_entries():
    with io.open(abspath('model.yml')) as file:
        data = yaml.load(file)
        for family_key in data:
            family = data[family_key]
            if type(family) is dict and 'type' in family:
                for genus_key in family:
                    print('\t', genus_key)
                    genus = family[genus_key]
                    if type(genus) is dict:
                        for species_key in genus:
                            species = genus[species_key]
                            if type(species) is dict and 'type' in species:
                                print('\t\t',species_key)
                            else:
                                print(species_key, 'species is not a dict')
                                return
                    else:
                        print(genus_key, 'genus is not a dict')
                        return
            else:
                print(family_key, 'family is not a dict')
                return

read_entries()