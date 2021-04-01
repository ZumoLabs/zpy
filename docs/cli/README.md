<div align="center">

**zpy cli usage**

</div>

<p align="center">
  <a href="app.zumolabs.ai">WebApp</a> •
  <a href="#Configuration">Configuration</a> •
  <a href="#List">List</a> •
  <a href="#Get">Get</a> •
  <a href="#Upload">Upload</a> •
  <a href="#Create">Create</a> •
  <a href="#Developer Commands">Developer Commands</a>
</p>

## Usage

The ZPY cli is meant as a command line tool to interact with assets on the zumo labs backend. The app can be found at [app.zumolabs.ai](https://app.zumolabs.ai) this command line covers the same functionality but allows developers to use command line to interact with zumo databases.

## Configuration

Authenticate with the backend : ```zpy login```

<p align="center"><img src="gif/login.gif?raw=true"/></p>

Verify CLI configuration : ```zpy config```

<p align="center"><img src="gif/config.gif?raw=true"/></p>

## List

List Datasets : ```zpy list datasets```

<p align="center"><img src="gif/listdataset.gif?raw=true"/></p>

List Sims : ```zpy list sims```

<p align="center"><img src="gif/listsim.gif?raw=true"/></p>

List Jobs : ```zpy list jobs```

<p align="center"><img src="gif/listjob.gif?raw=true"/></p>

## Get

Download Dataset : ```zpy get dataset <name> <dataset_type> /output/directory```

<p align="center"><img src="gif/getdataset.gif?raw=true"/></p>

Download Sim : ```zpy get sim <name> /output/directory```

<p align="center"><img src="gif/getsim.gif?raw=true"/></p>

## Upload

Upload Sim : ```zpy upload sim <name> /path/to/sim```

<p align="center"><img src="gif/uploadsim.gif?raw=true"/></p>

Upload Dataset : ```zpy upload dataset <name> /path/to/dataset```

<p align="center"><img src="gif/uploaddataset.gif?raw=true"/></p>

## Create

Create Dataset : ```zpy create dataset <name> <sim_name> kwargs```

<p align="center"><img src="gif/createdataset.gif?raw=true"/></p>

Create Sweep : ```zpy create sweep <name> <sim_name> <number_of_datasets> kwargs```

<p align="center"><img src="gif/createsweep.gif?raw=true"/></p>

Create Job : ```zpy create job <name> <operation> -d <dataset_id> -d <dataset_id> kwargs```

<p align="center"><img src="gif/createjob.gif?raw=true"/></p>

## Developer Commands

Switch target Environment : ```zpy env <newenv>```

<p align="center"><img src="gif/env.gif?raw=true"/></p>
