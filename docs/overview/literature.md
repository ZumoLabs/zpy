# Synthetic Data Literature

Many papers have been written about synthetic data over the years. If academic papers aren't your jam, we [publish articles](https://www.zumolabs.ai/blog) to explain synthetic data as simply as we can. Below are some key papers **organized by ...**

**... usecase:**

- Robotics: [1](#ref1), 
- Autonomous Vehicles:
- Humans: [2](#ref2),
- Space:
- ML Theory:
- Review:

**... year:**

- 2017: [2](#ref2),
- 2019: [1](#ref1),
- 2020:
- 2021:

The abstracts are also included with the paper links, so a good way to use this document is to `ctrl-F` the key words relevant to your usecase.

# Papers

### [Sim-to-Real via Sim-to-Sim: Data-efficient Robotic Grasping via Randomized-to-Canonical Adaptation Networks](https://arxiv.org/pdf/1812.07252.pdf) <a name="ref1"></a>

**Usecase** Robotic Grasping

**Year** 2019

**Abstract** Real world data, especially in the domain of robotics, is notoriously costly to collect. One way to circumvent this can be to leverage the power of simulation to produce large amounts of labelled data. However, training models on simulated images does not readily transfer to realworld ones. Using domain adaptation methods to cross this “reality gap” requires a large amount of unlabelled realworld data, whilst domain randomization alone can waste modeling power. In this paper, we present Randomizedto-Canonical Adaptation Networks (RCANs), a novel approach to crossing the visual reality gap that uses no realworld data. Our method learns to translate randomized rendered images into their equivalent non-randomized, canonical versions. This in turn allows for real images to also be translated into canonical sim images. We demonstrate the effectiveness of this sim-to-real approach by training a vision-based closed-loop grasping reinforcement learning agent in simulation, and then transferring it to the real world to attain 70% zero-shot grasp success on unseen objects, a result that almost doubles the success of learning the same task directly on domain randomization alone. Additionally, by joint finetuning in the real-world with only 5,000 real-world grasps, our method achieves 91%, attaining comparable performance to a state-of-the-art system trained with 580,000 real-world grasps, resulting in a reduction of real-world data by more than 99%.

---

### [Learning from Simulated and Unsupervised Images through Adversarial Training](https://arxiv.org/pdf/1612.07828.pdf) <a name="ref2"></a>

**Usecase** Human Gaze Estimation

**Year** 2017

**Abstract** With recent progress in graphics, it has become more tractable to train models on synthetic images, potentially avoiding the need for expensive annotations. However, learning from synthetic images may not achieve the desired performance due to a gap between synthetic and real image distributions. To reduce this gap, we propose Simulated+Unsupervised (S+U) learning, where the task is to learn a model to improve the realism of a simulator’s output using unlabeled real data, while preserving the annotation information from the simulator. We develop a method for S+U learning that uses an adversarial network similar to Generative Adversarial Networks (GANs), but with synthetic images as inputs instead of random vectors. We make several key modifications to the standard GAN algorithm to preserve annotations, avoid artifacts, and stabilize training: (i) a ‘self-regularization’ term, (ii) a local adversarial loss, and (iii) updating the discriminator using a history of refined images. We show that this enables generation of highly realistic images, which we demonstrate both qualitatively and with a user study. We quantitatively evaluate the generated images by training models for gaze estimation and hand pose estimation. We show a significant improvement over using synthetic images, and achieve state-of-the-art results on the MPIIGaze dataset without any labeled real data.

---

### [Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World](https://arxiv.org/pdf/1703.06907.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---

### [Deep Drone Racing: From Simulation to Reality with Domain Randomization](https://arxiv.org/pdf/1905.09727.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---
### [Structured Domain Randomization: Bridging the Reality Gap by Context-Aware Synthetic Data](https://arxiv.org/pdf/1810.10093.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---
 
### [Using Synthetic Data to Train Neural Networks is Model-Based Reasoning](https://arxiv.org/pdf/1703.00868.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---

### [Learning from Synthetic Humans](https://arxiv.org/pdf/1701.01370.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---

### [Multi Modal Semantic Segmentation using Synthetic Data](https://arxiv.org/pdf/1910.13676.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---

### [Semantic Understanding of Foggy Scenes with Purely Synthetic Data](https://arxiv.org/pdf/1910.03997.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---

### [Synthetic Data for Deep Learning](https://arxiv.org/pdf/1909.11512.pdf) <a name="ref"></a>

**Usecase**

**Year**

**Abstract**

---