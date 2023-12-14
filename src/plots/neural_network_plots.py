from datetime import datetime
import os
import sys
from matplotlib import pyplot as plt
import matplotlib
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnchoredText
from matplotlib.ticker import MultipleLocator

sys.path.append("..")
from prediction_neural_network.utilities import true_pred_occ_parking

plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams["legend.loc"] = 'lower right'


def set_tickslable(ax, label):
    ticklabels = [datetime.strftime(l,'%a %m-%d') for l in label]
    ax.set_xticklabels(ticklabels)
    xticks = ax.xaxis.get_major_ticks()
    temp_label = ''
    for index, label in enumerate(ax.get_xaxis().get_ticklabels()):
        if index >= len(ticklabels): #with multilable ticklabels[index] return: list index out of range
            xticks[index].set_visible(False)
        elif ticklabels[index] == temp_label or index == 0:
            if index == 0: temp_label = ticklabels[index]
            label.set_visible(False)  # hide labels
            xticks[index].set_visible(False)  # hide ticks where labels are hidden
        else:
            temp_label = ticklabels[index]


def one_step_ahead_subplot(ax, label, pred, truth, error, plot_error=True):
    date_label = [datetime.strftime(l, '%a %m-%d %H:%M') for l in label]
    ax.plot(date_label, pred, label='prediction',
            linestyle='--', linewidth=2, color='tab:blue')
    ax.plot(date_label, truth, label='truth', linewidth=3.5, color='tab:orange')

    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    if plot_error and error:
        ax.fill_between(date_label, pred - error, pred + error,
                        alpha=0.2, color='tab:blue')
    ax.set_xlim(date_label[0], date_label[-1])
    # ax.legend()
    return ax


def multi_steps_ahead_subplot(ax, multiple_label, multiple_pred, multiple_truth, error, plot_error=True):
    for label, pred, truth in zip(multiple_label, multiple_pred, multiple_truth):
        date_label = [datetime.strftime(l, '%a %m-%d %H') for l in label]
        ax.plot(date_label, pred, linestyle='--', linewidth=2)
        ax.plot(date_label, truth, linestyle='-', color='tab:orange', linewidth=3.5)
        if plot_error and error:
            ax.fill_between(date_label, pred - error, pred + error,
                            alpha=0.04, color='tab:blue')
    ax.grid(which='major', color='#CCCCCC', linestyle='-')
    left = datetime.strftime(multiple_label[0, 0], '%a %m-%d %H')
    right = datetime.strftime(multiple_label[-1, -1], '%a %m-%d %H')
    ax.set_xlim(left, right)
    return ax


def one_step_ahead_plot(label, pred, truth, path, capacity, error, percentual_error, hours_to_plot=None):
    label = label[:, 0]
    pred = pred[:, 0]
    truth = truth[:, 0]
    if hours_to_plot is not None:
        label = label[-hours_to_plot:]
        pred = pred[-hours_to_plot:]
        truth = truth[-hours_to_plot:]
    occ_parking_truth, occ_parking_pred, accuracy = true_pred_occ_parking(truth, pred, capacity, error, accuracy=True)
    fig, ax = build_plot(accuracy,  capacity, error)
    ax = one_step_ahead_subplot(ax, label, occ_parking_pred, occ_parking_truth, error)
    set_tickslable(ax, label)
    ax.set_title('One-step-ahead prediction on test set', size=18)
    plt.savefig(os.path.join(path,'1_step_prediction_{}.svg'.format(percentual_error)), bbox_inches='tight', format='svg')
    matplotlib.pyplot.close()


def multi_steps_ahead_plot(label, pred, truth, path, n_timesteps_out ,capacity, error, percentual_error,hours_to_plot=None):
    if hours_to_plot is not None:
        #hours_to_plot -= config.n_timesteps_out
        label = label[-hours_to_plot:]
        pred = pred[-hours_to_plot:, :]
        truth = truth[-hours_to_plot:]
    occ_parking_truth, occ_parking_pred, accuracy = true_pred_occ_parking(truth, pred, capacity, error, accuracy=True)
    fig, ax = build_plot(accuracy, capacity, error)
    ax = multi_steps_ahead_subplot(ax, label, occ_parking_pred, occ_parking_truth, error)
    set_tickslable(ax, label[:, 0])

    lines = [Line2D([0], [0], color='black', linewidth=2, linestyle='--'),
             Line2D([0], [0], color='orange', linewidth=3.5, linestyle='-')]
    labels = ['Predictions', 'Truth']
    ax.legend(lines, labels)
    ax.set_title('{}-steps-ahead predictions on test set'.format(n_timesteps_out), size=18)
    plt.savefig(os.path.join(path,'{}_step_prediction_{}.svg'.format(n_timesteps_out,percentual_error)), bbox_inches='tight', format='svg')
    matplotlib.pyplot.close()


def build_plot(accuracy, capacity, error):
    fig, ax = plt.subplots(figsize=(15, 8), sharex='col', sharey='row',
                                   gridspec_kw={'hspace': 0, 'wspace': 0})
    accuracy_text = AnchoredText('Parking accuracy={:.2f} (with error=±{})'.format(accuracy, error),
                                 loc='lower left')
    ax.add_artist(accuracy_text)
    ax.set(ylabel='Occupancy parking spot')
    ax.set(xlabel='Time')
    ax.yaxis.set_major_locator(MultipleLocator(round(capacity / 10)))
    fig.patch.set_facecolor('xkcd:white')
    return fig, ax