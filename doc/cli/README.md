<div align="center">

**CLI**

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

The ZPY cli is meant as a command line tool to interact with assets on the zumo labs backend. The app can be found at [app.zumolabs.ai](app.zumolabs.ai) this command line covers the same functionality but allows developers to use command line to interact with zumo databases.

## Configuration

Authenticate with the backend : ```zpy login```

<p align="center"><img src="gif/login.gif?raw=true"/></p>

Verify CLI configuration : ```zpy config```

<p align="center"><img src="gif/config.gif?raw=true"/></p>

## List

List Datasets : ```zpy list datasets```

<p align="center"><img src="gif/listdataset.gif?raw=true"/></p>

List Scenes : ```zpy list scenes```

<p align="center"><img src="gif/listscene.gif?raw=true"/></p>

List Jobs : ```zpy list jobs```

<p align="center"><img src="gif/listjob.gif?raw=true"/></p>

## Get

Download Dataset : ```zpy get dataset <name> <dataset_type> /output/directory```

<p align="center"><img src="gif/getdataset.gif?raw=true"/></p>

Download Scene : ```zpy get scene <name> /output/directory```

<p align="center"><img src="gif/getscene.gif?raw=true"/></p>

## Upload

Upload Scene : ```zpy upload scene <name> /path/to/scene```

<p align="center"><img src="gif/uploadscene.gif?raw=true"/></p>

Upload Dataset : ```zpy upload dataset <name> /path/to/dataset```

<p align="center"><img src="gif/uploaddataset.gif?raw=true"/></p>

## Create

Create Dataset : ```zpy create dataset <name> <scene_name> kwargs```

<p align="center"><img src="gif/createdataset.gif?raw=true"/></p>

Create Job : ```zpy create job <name> <operation> -d <dataset_id> -d <dataset_id> kwargs```

<p align="center"><img src="gif/createjob.gif?raw=true"/></p>

## Developer Commands

Switch target Environment : ```zpy env <newenv>```

<p align="center"><img src="gif/env.gif?raw=true"/></p>
