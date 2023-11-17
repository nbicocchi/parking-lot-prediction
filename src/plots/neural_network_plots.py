from datetime import datetime
import os
import sys
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnchoredText
from matplotlib.ticker import MultipleLocator

sys.path.append("..")
from prediction_neural_network import config
from prediction_neural_network.utilities import true_pred_occ_to_free_parking

plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams["legend.loc"] = 'lower right'


def set_tickslable(ax, label):

    ticklabels = [datetime.strftime(l,'%a %m-%d') for l in label]
    ax.set_xticklabels(ticklabels)
    xticks = ax.xaxis.get_major_ticks()
    temp_label = ''
    for index, label in enumerate(ax.get_xaxis().get_ticklabels()):
        if index >= len(ticklabels)-1: break
        if ticklabels[index] == temp_label or index == 0: #first date set invisibale to ger a clear timestamp on the x-axis
            if index == 0: temp_label = ticklabels[index]
            label.set_visible(False)  # hide labels
            xticks[index].set_visible(False)  # hide ticks where labels are hidden
        else:
            temp_label = ticklabels[index]


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
    
    # xticks = ax.xaxis.get_major_ticks()
    # for index, label in enumerate(ax.get_xaxis().get_ticklabels()):
    #     if index % 24 != 0: #first date set invisibale to ger a clear timestamp on the x-axis
    #         #print("disabilito")
    #         label.set_visible(False)  # hide labels
    #         xticks[index].set_visible(False)  # hide ticks where labels are hidden

    left = datetime.strftime(multiple_label[0, 0], '%a %m-%d %H')
    right = datetime.strftime(multiple_label[-1, -1], '%a %m-%d %H')
    ax.set_xlim(left, right)
    return ax


def one_step_ahead_plot(label, pred, truth, path,hours_to_plot=None):
    label = label[:, 0]
    pred = pred[:, 0]
    truth = truth[:, 0]
    if hours_to_plot is not None:
        label = label[-hours_to_plot:]
        pred = pred[-hours_to_plot:]
        truth = truth[-hours_to_plot:]
    free_parking_truth, free_parking_pred, accuracy = true_pred_occ_to_free_parking(truth, pred, accuracy=True)
    fig, ax = build_plot(accuracy)
    ax = one_step_ahead_subplot(ax, label, free_parking_pred, free_parking_truth)
    set_tickslable(ax, label)
    ax.set_title('One-step-ahead prediction on test set', size=18)
    plt.savefig(os.path.join(path,'1_step_prediction.svg'), bbox_inches='tight', format='svg')
    #plt.show()


def multi_steps_ahead_plot(label, pred, truth, path, hours_to_plot=None):
    if hours_to_plot is not None:
        #hours_to_plot -= config.n_timesteps_out
        label = label[-hours_to_plot:]
        pred = pred[-hours_to_plot:, :]
        truth = truth[-hours_to_plot:]
    free_parking_truth, free_parking_pred, accuracy = true_pred_occ_to_free_parking(truth, pred, accuracy=True)
    fig, ax = build_plot(accuracy)
    ax = multi_steps_ahead_subplot(ax, label, free_parking_pred, free_parking_truth)
    set_tickslable(ax, label[:, 0])

    lines = [Line2D([0], [0], color='black', linewidth=2, linestyle='--'),
             Line2D([0], [0], color='orange', linewidth=3.5, linestyle='-')]
    labels = ['Predictions', 'Truth']
    ax.legend(lines, labels)
    ax.set_title('{}-steps-ahead predictions on test set'.format(config.n_timesteps_out), size=18)
    plt.savefig(os.path.join(path,'8_step_prediction.svg'), bbox_inches='tight', format='svg')


def build_plot(accuracy):
    fig, ax = plt.subplots(figsize=(15, 8), sharex='col', sharey='row',
                                   gridspec_kw={'hspace': 0, 'wspace': 0})
    accuracy_text = AnchoredText('Parking accuracy={:.2f} (with error=±{})'.format(accuracy, config.error),
                                 loc='lower left')
    ax.add_artist(accuracy_text)
    ax.set(ylabel='Free parking spot')
    ax.set(xlabel='Time')
    ax.yaxis.set_major_locator(MultipleLocator(round(config.n_sensors / 10)))
    fig.patch.set_facecolor('xkcd:white')
    return fig, ax