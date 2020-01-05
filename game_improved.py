from __future__ import print_function

import multiprocessing
import os

import neat
import numpy as np
import gym

from skimage.measure import block_reduce
import matplotlib.pyplot as plt
import custom_report

env = gym.make('CarRacing-v0')

NUM_GENERATIONS = 1000

def map_image(pixel):
    if pixel[1] < 200:
        return 1
    return 0


def preprocess(frame):
    """
    This function receives a frame of the game and performs mean pooling in kernels od 2x2x3, to reduce dimensionality. Resulting 
    """
    # Simplify the map by setting the road to 1 and everything else to 0
    frame = np.array([[map_image(pixel) for pixel in row] for row in frame])
    frame = frame[:83, :]
    frame = block_reduce(frame, (5, 5), np.mean)
    frame = frame.flatten()
    return frame


def eval_network(net, frame):
#     print(frame.shape)
    assert (frame.shape == (340,))
    result = net.activate(frame)
    assert (len(result) == 3)
    return result

def eval_genome(genome, config):
    """
    This function will be run in parallel by ParallelEvaluator.  It takes two
    arguments (a single genome and the genome class configuration data) and
    should return one float (that genome's fitness).

    """
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    total_reward = 0.0
    frame = env.reset()
    frame = preprocess(frame)
    last_frame = frame
    action = eval_network(net, frame)
    done = False
    while not done:
        env.render()
        frame, reward, done, _ = env.step(action)
        total_reward += reward
        frame = preprocess(frame)
        # If the road disappears of the map or the car stops, exit the game with reward -= 80
        if not frame.any() or np.array_equal(last_frame, frame):
            done = True
            total_reward -= 80
        action = eval_network(net, frame)
#         print(action)
        last_frame = frame

    return total_reward

def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    
    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)
    # Or load one from a checkpointer
#     p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-29')

    # Add a stdout reporter to show progress in the terminal.
    custom_stats = custom_report.StdOutReporter()
    # In case you want to load it from a checkpointer add:
#     custom_stats.load('neat-stats-29')

    p.add_reporter(custom_stats)
#     stats = neat.StatisticsReporter()
#     p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(1))



    # Run for up to 300 generations.
    pe = neat.ParallelEvaluator(multiprocessing.cpu_count(), eval_genome)
    winner = p.run(pe.evaluate, NUM_GENERATIONS)

    custom_stats.save_table('stats_table')

#     visualize.draw_net(config, winner, True)
#     visualize.plot_stats(stats, ylog=False, view=True)
#     visualize.plot_species(stats, view=True)


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'example_config_file')
    run(config_path)