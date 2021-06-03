# Synthetic Data Literature

Many papers have been written about synthetic data over the years. If academic papers aren't your jam, we [publish articles](https://www.zumolabs.ai/blog) to explain synthetic data as simply as we can. Below are some key papers **organized by ...**

**... usecase:**

- Robotics: [1](#ref1), [3](#ref3), [4](#ref4),
- Autonomous Vehicles: [5](#ref5), [8](#ref8), [9](#ref9),
- Humans: [2](#ref2), [7](#ref7),
- Space:
- ML Theory: [6](#ref6),
- Overview: [10](#ref10),

**... year:**

- 2017: [2](#ref2), [3](#ref3), [6](#ref6),
- 2018: [7](#ref7),
- 2019: [1](#ref1), [4](#ref4), [8](#ref8),
- 2020: [5](#ref5), [9](#ref9),
- 2021:

**TIP** The abstracts are also included with the paper links, so a good way to use this document is to `ctrl-F` the key words relevant to your usecase.

# Papers

## [Sim-to-Real via Sim-to-Sim: Data-efficient Robotic Grasping via Randomized-to-Canonical Adaptation Networks](https://arxiv.org/pdf/1812.07252.pdf) <a name="ref1"></a>

**Usecase** Robotic Grasping

**Year** 2019

**Abstract** Real world data, especially in the domain of robotics, is notoriously costly to collect. One way to circumvent this can be to leverage the power of simulation to produce large amounts of labelled data. However, training models on simulated images does not readily transfer to realworld ones. Using domain adaptation methods to cross this “reality gap” requires a large amount of unlabelled realworld data, whilst domain randomization alone can waste modeling power. In this paper, we present Randomizedto-Canonical Adaptation Networks (RCANs), a novel approach to crossing the visual reality gap that uses no realworld data. Our method learns to translate randomized rendered images into their equivalent non-randomized, canonical versions. This in turn allows for real images to also be translated into canonical sim images. We demonstrate the effectiveness of this sim-to-real approach by training a vision-based closed-loop grasping reinforcement learning agent in simulation, and then transferring it to the real world to attain 70% zero-shot grasp success on unseen objects, a result that almost doubles the success of learning the same task directly on domain randomization alone. Additionally, by joint finetuning in the real-world with only 5,000 real-world grasps, our method achieves 91%, attaining comparable performance to a state-of-the-art system trained with 580,000 real-world grasps, resulting in a reduction of real-world data by more than 99%.

---

## [Learning from Simulated and Unsupervised Images through Adversarial Training](https://arxiv.org/pdf/1612.07828.pdf) <a name="ref2"></a>

**Usecase** Human Gaze Estimation

**Year** 2017

**Abstract** With recent progress in graphics, it has become more tractable to train models on synthetic images, potentially avoiding the need for expensive annotations. However, learning from synthetic images may not achieve the desired performance due to a gap between synthetic and real image distributions. To reduce this gap, we propose Simulated+Unsupervised (S+U) learning, where the task is to learn a model to improve the realism of a simulator’s output using unlabeled real data, while preserving the annotation information from the simulator. We develop a method for S+U learning that uses an adversarial network similar to Generative Adversarial Networks (GANs), but with synthetic images as inputs instead of random vectors. We make several key modifications to the standard GAN algorithm to preserve annotations, avoid artifacts, and stabilize training: (i) a ‘self-regularization’ term, (ii) a local adversarial loss, and (iii) updating the discriminator using a history of refined images. We show that this enables generation of highly realistic images, which we demonstrate both qualitatively and with a user study. We quantitatively evaluate the generated images by training models for gaze estimation and hand pose estimation. We show a significant improvement over using synthetic images, and achieve state-of-the-art results on the MPIIGaze dataset without any labeled real data.

---

## [Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World](https://arxiv.org/pdf/1703.06907.pdf) <a name="ref3"></a>

**Usecase** Robotic Grasping

**Year** 2017

**Abstract** Bridging the ‘reality gap’ that separates simulated robotics from experiments on hardware could accelerate robotic research through improved data availability. This paper explores domain randomization, a simple technique for training models on simulated images that transfer to real images by randomizing rendering in the simulator. With enough variability in the simulator, the real world may appear to the model as just another variation. We focus on the task of object localization, which is a stepping stone to general robotic manipulation skills. We find that it is possible to train a real-world object detector that is accurate to 1.5 cm and robust to distractors and partial occlusions using only data from a simulator with non-realistic random textures. To demonstrate the capabilities of our detectors, we show they can be used to perform grasping in a cluttered environment. To our knowledge, this is the first successful transfer of a deep neural network trained only on simulated RGB images (without pre-training on real images) to the real world for the purpose of robotic control.

---

## [Deep Drone Racing: From Simulation to Reality with Domain Randomization](https://arxiv.org/pdf/1905.09727.pdf) <a name="ref4"></a>

**Usecase** Drone Racing

**Year** 2019

**Abstract** Dynamically changing environments, unreliable state estimation, and operation under severe resource constraints are fundamental challenges that limit the deployment of small autonomous drones. We address these challenges in the context of autonomous, vision-based drone racing in dynamic environments. A racing drone must traverse a track with possibly moving gates at high speed. We enable this functionality by combining the performance of a state-of-the-art planning and control system with the perceptual awareness of a convolutional neural network (CNN). The resulting modular system is both platform- and domain-independent: it is trained in simulation and deployed on a physical quadrotor without any fine-tuning. The abundance of simulated data, generated via domain randomization, makes our system robust to changes of illumination and gate appearance. To the best of our knowledge, our approach is the first to demonstrate zero-shot sim-to-real transfer on the task of agile drone flight. We extensively test the precision and robustness of our system, both in simulation and on a physical platform, and show significant improvements over the state of the art.

---
## [Structured Domain Randomization: Bridging the Reality Gap by Context-Aware Synthetic Data](https://arxiv.org/pdf/1810.10093.pdf) <a name="ref5"></a>

**Usecase** Autonomous Vehicles

**Year** 2020

**Abstract**  We present structured domain randomization (SDR), a variant of domain randomization (DR) that takes into account the structure and context of the scene. In contrast to DR, which places objects and distractors randomly according to a uniform probability distribution, SDR places objects and distractors randomly according to probability distributions that arise from the specific problem at hand. In this manner, SDRgenerated imagery enables the neural network to take the context around an object into consideration during detection. We demonstrate the power of SDR for the problem of 2D bounding box car detection, achieving competitive results on real data after training only on synthetic data. On the KITTI easy, moderate, and hard tasks, we show that SDR outperforms other approaches to generating synthetic data (VKITTI, Sim 200k, or DR), as well as real data collected in a different domain (BDD100K). Moreover, synthetic SDR data combined with real KITTI data outperforms real KITTI data alone.

---
 
## [Using Synthetic Data to Train Neural Networks is Model-Based Reasoning](https://arxiv.org/pdf/1703.00868.pdf) <a name="ref6"></a>

**Usecase** ML Theory

**Year** 2017

**Abstract** We draw a formal connection between using synthetic training data to optimize neural network parameters and approximate, Bayesian, model-based reasoning. In particular, training a neural network using synthetic data can be viewed as learning a proposal distribution generator for approximate inference in the synthetic-data generative model. We demonstrate this connection in a recognition task where we develop a novel Captcha-breaking architecture and train it using synthetic data, demonstrating both state-of-the-art performance and a way of computing task-specific posterior uncertainty. Using a neural network trained this way, we also demonstrate successful breaking of real-world Captchas currently used by Facebook and Wikipedia. Reasoning from these empirical results and drawing connections with Bayesian modeling, we discuss the robustness of synthetic data results and suggest important considerations for ensuring good neural network generalization when training with synthetic data.

---

## [Learning from Synthetic Humans](https://arxiv.org/pdf/1701.01370.pdf) <a name="ref7"></a>

**Usecase** Human Pose Detection

**Year** 2018

**Abstract** Estimating human pose, shape, and motion from images and videos are fundamental challenges with many applications. Recent advances in 2D human pose estimation use large amounts of manually-labeled training data for learning convolutional neural networks (CNNs). Such data is time consuming to acquire and difficult to extend. Moreover, manual labeling of 3D pose, depth and motion is impractical. In this work we present SURREAL (Synthetic hUmans foR REAL tasks): a new large-scale dataset with synthetically-generated but realistic images of people rendered from 3D sequences of human motion capture data. We generate more than 6 million frames together with ground truth pose, depth maps, and segmentation masks. We show that CNNs trained on our synthetic dataset allow for accurate human depth estimation and human part segmentation in real RGB images. Our results and the new dataset open up new possibilities for advancing person analysis using cheap and large-scale synthetic data.

---

## [Multi Modal Semantic Segmentation using Synthetic Data](https://arxiv.org/pdf/1910.13676.pdf) <a name="ref8"></a>

**Usecase** Autonomous Vehicles

**Year** 2019

**Abstract** Semantic understanding of scenes in threedimensional space (3D) is a quintessential part of robotics oriented applications such as autonomous driving as it provides geometric cues such as size, orientation and true distance of separation to objects which are crucial for taking mission critical decisions. As a first step, in this work we investigate the possibility of semantically classifying different parts of a given scene in 3D by learning the underlying geometric context in addition to the texture cues BUT in the absence of labelled real-world datasets. To this end we generate a large number of synthetic scenes, their pixel-wise labels and corresponding 3D representations using CARLA software framework. We then build a deep neural network that learns underlying category specific 3D representation and texture cues from color information of the rendered synthetic scenes. Further on we apply the learned model on different real world datasets to evaluate its performance. Our preliminary investigation of results show that the neural network is able to learn the geometric context from synthetic scenes and effectively apply this knowledge to classify each point of a 3D representation of a scene in real-world.

---

## [Semantic Understanding of Foggy Scenes with Purely Synthetic Data](https://arxiv.org/pdf/1910.03997.pdf) <a name="ref9"></a>

**Usecase** Autonomous Vehicles

**Year** 2020

**Abstract** This work addresses the problem of semantic scene understanding under foggy road conditions. Although marked progress has been made in semantic scene understanding over the recent years, it is mainly concentrated on clear weather outdoor scenes. Extending semantic segmentation methods to adverse weather conditions like fog is crucially important for outdoor applications such as self-driving cars. In this paper, we propose a novel method, which uses purely synthetic data to improve the performance on unseen realworld foggy scenes captured in the streets of Zurich and its surroundings. Our results highlight the potential and power of photo-realistic synthetic images for training and especially fine-tuning deep neural nets. Our contributions are threefold, 1) we created a purely synthetic, high-quality foggy dataset of 25,000 unique outdoor scenes, that we call Foggy Synscapes and plan to release publicly 2) we show that with this data we outperform previous approaches on real-world foggy test data 3) we show that a combination of our data and previously used data can even further improve the performance on real-world foggy data.

---

## [Synthetic Data for Deep Learning](https://arxiv.org/pdf/1909.11512.pdf) <a name="ref10"></a>

**Usecase** Overview

**Year** 2019

**Abstract** Synthetic data is an increasingly popular tool for training deep learning models, especially in computer vision but also in other areas. In this work, we attempt to provide a comprehensive survey of the various directions in the development and application of synthetic data. First, we discuss synthetic datasets for basic computer vision problems, both low-level (e.g., optical flow estimation) and high-level (e.g., semantic segmentation), synthetic environments and datasets for outdoor and urban scenes (autonomous driving), indoor scenes (indoor navigation), aerial navigation, simulation environments for robotics, applications of synthetic data outside computer vision (in neural programming, bioinformatics, NLP, and more); we also survey the work on improving synthetic data development and alternative ways to produce it such as GANs. Second, we discuss in detail the synthetic-to-real domain adaptation problem that inevitably arises in applications of synthetic data, including syntheticto-real refinement with GAN-based models and domain adaptation at the feature/model level without explicit data transformations. Third, we turn to privacy-related applications of synthetic data and review the work on generating synthetic datasets with differential privacy guarantees. We conclude by highlighting the most promising directions for further work in synthetic data studies.

---