from blqt.rl_envs.vb_env import *


if __name__ == '__main__':
    config = sac.DEFAULT_CONFIG.copy()
    config["env"] = VBEnv_V3

    config["env_config"] = {
        "data_path_1min" : "/tmp/pycharm_project_22/data/bitmex/XBTUSD_1H.csv",
        "data_path_1day": "/tmp/pycharm_project_22/data/bitmex/XBTUSD_1D.csv",
        "from_timeindex" : -np.inf,
        "to_timeindex" : np.inf,
        "k" : 0.6,
    }

    config["framework"] = "torch"
    config["num_workers"] = 11

    tune.run(
        sac.SACTrainer,
        config=config,
        checkpoint_freq=100,
        checkpoint_at_end=True,
        local_dir="./log",
    )