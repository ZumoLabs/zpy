Domain randomization is a popular technique when generating synthetic data. The key concept behind domain randomization is increasing the variance of certain data parameters in the training set beyond what is seen in the test set. These data parameters may include lighting, camera viewpoint, and asset materials. Models trained on a domain randomized synthetic dataset are more general and suffer less from the sim2real gap.

![How the increased variance of domain randomization decreases the sim2real gap.](https://github.com/ZumoLabs/zpy/raw/main/docs/assets/domain_randomization.png)