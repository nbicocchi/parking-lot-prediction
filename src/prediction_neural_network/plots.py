from datetime import datetime

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnchoredText
from matplotlib.ticker import MultipleLocator

import neural_network.config as config
from neural_network.data_processing import process
from neural_network.utilities import occupancy_to_free_parking, true_pred_occ_to_free_parking

plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams["legend.loc"] = 'lower right'


def one_step_ahead_subplot(ax, label, pred, truth, plot_error=True):
    date_label = [datetime.strftime(l, '%a %m-%d %H:%M') for l in label]
    ax.plot(date_label, pred, label='prediction',
            linestyle='--', linewidth=2, color='tab:blue')
    ax.plot(date_label, truth, label='truth', linewidth=3.5, color='tab:orange')
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    if plot_error and config.error:
        ax.fill_between(date_label, pred - config.error, pred + config.error,
                        alpha=0.2, color='tab:blue')
    ax.set_xlim(date_label[0], date_label[-1])
    # ax.legend()
    return ax


def multi_steps_ahead_subplot(ax, multiple_label, multiple_pred, multiple_truth, plot_error=True):
    for label, pred, truth in zip(multiple_label, multiple_pred, multiple_truth):
        date_label = [datetime.strftime(l, '%a %m-%d %H') for l in label]
        ax.plot(date_label, pred, linestyle='--', linewidth=2)
        ax.plot(date_label, truth, linestyle='-', color='tab:orange', linewidth=3.5)
        if plot_error and config.error:
            ax.fill_between(date_label, pred - config.error, pred + config.error,
                            alpha=0.04, color='tab:blue')
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    left = datetime.strftime(multiple_label[0, 0], '%a %m-%d %H')
    right = datetime.strftime(multiple_label[-1, -1], '%a %m-%d %H')
    ax.set_xlim(left, right)
    return ax


def one_step_ahead_plot(label, pred, truth, hours_to_plot=None):
    label = label[:, 0]
    pred = pred[:, 0]
    truth = truth[:, 0]
    if hours_to_plot is not None:
        label = label[-hours_to_plot:]
        pred = pred[-hours_to_plot:]
        truth = truth[-hours_to_plot:]
    free_parking_truth, free_parking_pred, accuracy = true_pred_occ_to_free_parking(truth, pred, accuracy=True)
    fig, (ax1, ax2) = build_double_plot(accuracy)
    ax2 = one_step_ahead_subplot(ax2, label, pred, truth, plot_error=False)
    ax2 = one_step_ahead_subplot(ax2, label, free_parking_pred, free_parking_truth)
    ax2.set(ylabel='Free parking spot')
    ax2.set(xlabel='Time')
    ax1.set_title('One-step-ahead prediction on test set', size=18)
    plt.savefig('1_step_prediction_NEW.svg', bbox_inches='tight', format='svg')
    plt.show()


def multi_steps_ahead_plot(label, pred, truth, hours_to_plot=None):
    if hours_to_plot is not None:
        hours_to_plot -= config.n_timesteps_out
        label = label[-hours_to_plot:]
        pred = pred[-hours_to_plot:, :]
        truth = truth[-hours_to_plot:]
    free_parking_truth, free_parking_pred, accuracy = true_pred_occ_to_free_parking(truth, pred, accuracy=True)
    fig, (ax1, ax2) = build_double_plot(accuracy)
    ax1 = multi_steps_ahead_subplot(ax1, label, pred, truth, plot_error=False)
    ax2 = multi_steps_ahead_subplot(ax2, label, free_parking_pred, free_parking_truth)
    ax2.set(ylabel='Free parking spot')
    ax2.set(xlabel='Time')
    lines = [Line2D([0], [0], color='black', linewidth=2, linestyle='--'),
             Line2D([0], [0], color='orange', linewidth=3.5, linestyle='-')]
    labels = ['Predictions', 'Truth']
    ax1.legend(lines, labels)
    ax2.legend(lines, labels)
    ax1.set_title('{}-steps-ahead predictions on test set'.format(config.n_timesteps_out), size=18)
    plt.savefig('8_step_prediction_NEW.svg', bbox_inches='tight', format='svg', size=(15, 8))
    plt.show()


def build_double_plot(accuracy):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8), sharex='col', sharey='row',
                                   gridspec_kw={'hspace': 0, 'wspace': 0})
    accuracy_text = AnchoredText('Parking accuracy={:.2f} (with error=±{})'.format(accuracy, config.error),
                                 loc='lower left')
    ax2.add_artist(accuracy_text)
    ax1.set(ylabel='Percentage')
    ax2.set(ylabel='Free parking spot')
    ax2.set(xlabel='Time')
    ax1.yaxis.set_major_locator(MultipleLocator(0.05))
    ax2.yaxis.set_major_locator(MultipleLocator(round(config.n_sensors / 10)))
    fig.patch.set_facecolor('xkcd:white')
    return fig, (ax1, ax2)


def unseen_data_plot(df, pred, pred_timestamps):
    data, timestamps = process(df, labels=False)
    data_labels = [datetime.strftime(l, '%a %m-%d %H') for l in timestamps]
    pred_labels = [datetime.strftime(l, '%a %m-%d %H') for l in pred_timestamps]
    data = data[..., -1].squeeze()
    data = occupancy_to_free_parking(data)
    pred = occupancy_to_free_parking(pred)

    fig, ax = plt.subplots(1, 1, figsize=(25, 11))
    ax.set(ylabel='free parking spot')
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    fig.patch.set_facecolor('xkcd:white')
    plt.xticks(rotation=90)
    plt.plot(data_labels, data, color='tab:orange', linewidth=3.5)
    plt.plot(pred_labels, pred, linestyle='--', linewidth=2.5, color='tab:blue')
    plt.xlim(left=data_labels[0], right=pred_labels[-1])
    x = [data_labels[-1], pred_labels[0], pred_labels[0]]
    y = [data[-1], pred[0] + config.error, pred[0] - config.error]
    plt.fill(x, y, color='tab:blue', alpha=0.4)
    plt.fill_between(pred_labels, pred - config.error, pred + config.error, color='tab:blue', alpha=0.4)
    ax.set_title('{}-steps-ahead prediction on last known data'.format(config.n_timesteps_out), size=18)
    plt.show()
