# Standard and External lib imports
from bokeh.mpl import to_bokeh
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file, output_notebook, ColumnDataSource
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.models import ( Text, PanTool, WheelZoomTool, LinearAxis,
                           SingleIntervalTicker, Range1d,  Plot,
                           Text, Circle, HoverTool, Triangle)
from math import ceil
from numpy import pi as PI

import operator
import os
import itertools

#TODO: Ugh.. this file/module needs a cleanup
# Custom imports
from . import utils

# Axis settings for Bokeh plots
AXIS_FORMATS = dict(
    minor_tick_in=None,
    minor_tick_out=None,
    major_tick_in=None,
    major_label_text_font_size="10pt",
    major_label_text_font_style="normal",
    axis_label_text_font_size="10pt",

    axis_line_color='#AAAAAA',
    major_tick_line_color='#AAAAAA',
    major_label_text_color='#666666',

    major_tick_line_cap="round",
    axis_line_cap="round",
    axis_line_width=1,
    major_tick_line_width=1,)

BOKEH_TOOLS = "resize,crosshair,pan,wheel_zoom,box_zoom,reset,tap,previewsave,box_select,poly_select,lasso_select"

def genColors(n, ptype='magma'):
    """
    """
    from bokeh.palettes import magma, inferno, plasma, viridis
    if ptype=='magma':
        return magma(n)
    elif ptype == 'inferno':
        return inferno(n)
    elif ptype == 'plasma':
        return plasma(n)
    else:
        return viridis(n)

def plot_patches(bandx, bandy, **kwargs):
    p = figure(x_range=(0, 10), y_range=(0, 10), title=kwargs.pop('title'))
    p.xaxis.axis_label=kwargs.pop('xlabel')
    p.yaxis.axis_label=kwargs.pop('ylabel')
    p.patch(bandx, bandy, **kwargs)
    return p

def show_image(image):
    p = figure(x_range=(0, 10), y_range=(0, 10))
    p.image(image=[image], x=0, y=0, dw=10, dh=10, palette='Spectral11')
    return p

def show_tree_model(model, model_type='tree'):
    assert model_type in ['tree', 'randomforest', 'xgboost']
    from sklearn import tree
    import pydotplus
    import tempfile
    from skimage import io
    #assert isinstance(model, tree.DecisionTreeClassifier)
    if model_type == 'tree':
        fout = tempfile.NamedTemporaryFile(suffix='.png')
        dot_fname = '.'.join([fout.name.split('.')[0], 'dot'])
        dot_data = tree.export_graphviz(model, out_file=dot_fname)
        os.system('dot -Tpng %s -o %s'%(dot_fname, fout.name))
        show(show_image(io.imread(fout.name)))
        os.remove(dot_fname)
    elif model_type == 'randomforest':
        graph_plots = list()
        if len(model.estimators_) > 10:
            print("Sorry more that 10 trees can't be displayed")
            return
        for tree_model in model.estimators_:
            fout = tempfile.NamedTemporaryFile(suffix='.png')
            dot_fname = '.'.join([fout.name.split('.')[0], 'dot'])
            dot_data = tree.export_graphviz(tree_model, out_file=dot_fname)
            os.system('dot -Tpng %s -o %s'%(dot_fname, fout.name))
            graph_plots.append(show_image(io.imread(fout.name)))
        grid = gridplot(list(utils.chunks(graph_plots, size=3)))
        show(grid)
        os.remove(dot_fname)
    else:
        #It must be xgboost
        import xgboost
        xgboost.to_graphviz(model)
        fout = tempfile.NamedTemporaryFile(suffix='.png')
        dot_fname = '.'.join([fout.name.split('.')[0], 'dot'])
        dot_data = tree.export_graphviz(tree_model, out_file=dot_fname)
        os.system('dot -Tpng %s -o %s'%(dot_fname, fout.name))
        show(show_image(io.imread(fout.name)))
        os.remove(dot_fname)

def show_model_interpretation(model, model_type='randomforest'):
    #TODO: Use lime
    import lime
    pass

def lineplot(df, xcol, ycol, fig=None, label=None, color=None, title=None, **kwargs):
    if not title:
        title = "%s Vs %s" %(xcol, ycol)
    if label:
        label = label + ycol
    else:
        label = ycol
    if not fig:
        fig = figure(title=title)
    if not color:
        color=(100,100,255, 1)
    fig.line(df[xcol], df[ycol], color=color, legend=label)
    fig.legend.location = "top_left"
    return fig


def timestamp(datetimeObj):
    timestamp = (datetimeObj - datetime(1970, 1, 1)).total_seconds()
    return timestamp


def month_year_format(datetimeObj):
    return str(datetimeObj.strftime("%b-%Y"))


def plot_twin_y_axis_scatter(conn, query1=None, query2=None,
                             xy1={}, xy2={}):
    """
    Plots twin y axis scatter plot you just have to give conn sqlalchemy obj and
    two query/dictionary of x and y values
    :param conn: Sqlaclhemy connection object
    :param query1: query 1 for x and y1
    :param query2: query 2 for x and y2
    :param xy1: dictionary containing x and y key values
    :param xy2: dictionary containing x and y key values
    :return: Bokeh plot object (script,div)
    """

    if query1:
        result = conn.execute(query1)
        plot_data1 = {'x': [], 'y': []}
        for row in result:
            if row[0] and row[1]:
                plot_data1['x'].append(float(row[0]))
                plot_data1['y'].append(str(row[1]))
    else:
        if isinstance(xy1, dict) and xy1:
            plot_data1 = xy1
        else:
            raise ValueError('Parameters values not given properly')

    if query2:
        result = conn.execute(query2)
        plot_data2 = {'x': [], 'y': []}
        for row in result:
            if row[0] and row[1]:
                plot_data2['x'].append(float(row[0]))
                plot_data2['y'].append(str(row[1]))
    else:
        if isinstance(xy2, dict) and xy2:
            plot_data2 = xy2
        else:
            raise ValueError('Parameters values not given properly')

    renderer_source = ColumnDataSource({'x': plot_data1['x'], 'y': plot_data1['y']})
    renderer_source2 = ColumnDataSource({'x': plot_data2['x'], 'y': plot_data2['y']})

    bokeh_plot = BokehTwinLinePlot(plot_data1, plot_data2,
                                   xlabel="No. of Accounts",
                                   ylabel="No. of. Leave Transactions",
                                   ylabel2="No. of services")
    plot = bokeh_plot.get_plot()
    plot = bokeh_plot.add_text(plot)
    # Add the triangle
    triangle_glyph = Triangle(
        x='x', y='y', size=15,
        fill_color='#4682B4', fill_alpha=0.8,
        line_color='#4682B4', line_width=0.5, line_alpha=0.5)
    # Add the circle
    circle_glyph = Circle(
        x='x', y='y', size=15,
        fill_color='#d24726', fill_alpha=0.8,
        line_color='#d24726', line_width=0.5, line_alpha=0.5)
    triangle_renderer = plot.add_glyph(renderer_source, triangle_glyph)
    circle_renderer = plot.add_glyph(renderer_source2, circle_glyph, y_range_name="y_range2")

    # Add the hover (only against the circle and not other plot elements)
    tooltips = "@index"
    plot.add_tools(HoverTool(tooltips=tooltips, renderers=[triangle_renderer, circle_renderer]))
    plot.add_tools(PanTool(), WheelZoomTool())
    return plot

class BokehTwinLinePlot(object):
    """
    Class for creating basic bokeh structure of two y axis and one x axis
    """

    def __init__(self, plot_data1, plot_data2, xlabel='x', ylabel='y', ylabel2='y2'):
        self.plot_data1 = plot_data1
        self.plot_data2 = plot_data2
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.ylabel2 = ylabel2

    def get_plot(self):
        """
        Creates the basic bokeh plot with xrange, y range
        :return: Boekh plot obj.
        """
        min_x_range, max_x_range = self.get_x_ranges()
        min_y_range, max_y_range = self.get_y_ranges(self.plot_data1)
        min_y2_range, max_y2_range = self.get_y_ranges(self.plot_data2)
        xdr = Range1d(min_x_range-(min_x_range/1.2), max_x_range+(max_x_range/1.2))
        ydr = Range1d(min_y_range-(min_y_range/1.2), max_y_range+(max_y_range/1.2))
        ydr2 = Range1d(min_y2_range-(min_y2_range/10), max_y2_range+(max_y2_range/10))
        plot = Plot(
            x_range=xdr,
            y_range=ydr,
            extra_y_ranges={"y_range2":ydr2},
            title="",
            plot_width=550,
            plot_height=550,
            outline_line_color=None,
            toolbar_location=None,
        )
        return plot

    def add_axes(self, plot):
        """
        Adds axis to Bokeh plot Obj
        :param plot: Bokeh plot obj. from get_plot method
        :return: Bokeh plot obj
        """
        min_x_range, max_x_range = self.get_x_ranges()
        min_y_range, max_y_range = self.get_y_ranges(self.plot_data1)
        min_y2_range, max_y2_range = self.get_y_ranges(self.plot_data2)
        x_interval = utils.roundup(max_x_range)
        y_interval = utils.roundup(max_y_range)
        y2_interval = utils.roundup(max_y2_range)
        xaxis = LinearAxis(SingleIntervalTicker(interval=x_interval), axis_label=self.xlabel, **AXIS_FORMATS)
        yaxis = LinearAxis(SingleIntervalTicker(interval=y_interval), axis_label=self.ylabel, **AXIS_FORMATS)
        yaxis2 = LinearAxis(SingleIntervalTicker(interval=y2_interval), y_range_name="y_range2", axis_label=self.ylabel2, **AXIS_FORMATS)
        plot.add_layout(xaxis, 'below')
        plot.add_layout(yaxis, 'left')
        plot.add_layout(yaxis2, 'right')
        return plot

    def add_text(self, plot):
        """
        Adds text to Bokeh plot
        :param plot: Bokeh plot obj.
        :return: Bokeh plot obj.
        """
        plot = self.add_axes(plot)
        return plot

    def get_x_ranges(self):
        """
        get the minimum and maximum values of x
        :return: Minimum x value, Maximum x value
        """
        plot_data1_x = list(self.plot_data1['x'])
        plot_data2_x = list(self.plot_data2['x'])
        if not plot_data1_x:
            plot_data1_x = [0]
        if not plot_data2_x:
            plot_data2_x = [0]
        min_x_range = min([min(plot_data1_x),min(plot_data2_x)])
        max_x_range = max([max(plot_data1_x), max(plot_data2_x)])

        return min_x_range, max_x_range

    def get_y_ranges(self, plot_data):
        """
        get the minimum and maximum values of y
        :return: Minimum y value, Maximum y value
        """
        plot_data_y = map(float, list(plot_data['y']))
        if not plot_data_y:
            plot_data_y = [0]
        min_y_range = min(plot_data_y)
        max_y_range = max(plot_data_y)
        return min_y_range, max_y_range


def histogram(histDF,values, bayesian_bins=False,**kwargs):
    if not bayesian_bins:
        from bokeh.charts import Histogram
        return Histogram(histDF[values], **kwargs)
    else:
        import numpy as np
        bins = utils.bayesian_blocks(histDF[values])
        p1 = figure(title=kwargs.pop('title', 'Histogram of %s'%values),
                    tools="save", background_fill_color="#E8DDCB")
        hist,edges = np.histogram(histDF[values], bins=bins)
        p1.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
                fill_color="#036564", line_color="#033649")
        p1.legend.location = "top_left"
        p1.xaxis.axis_label = 'x'
        p1.yaxis.axis_label = 'Frequency'
        return p1


def barplot(barDF, xlabel, ylabel, title="Bar Plot",
                            agg='sum', **kwargs):
    from bokeh.charts import Bar
    barplot = Bar(barDF, xlabel, values=ylabel, agg=agg, title=title, **kwargs)
    return barplot

def boxplot(boxDF, values_label, xlabel, title="boxplot", **kwargs):
    from bokeh.charts import BoxPlot
    boxplot = BoxPlot(boxDF, values=values_label, label=xlabel, color=xlabel, title=title, **kwargs)
    return boxplot

def heatmap(heatMapDF,xlabel, ylabel, value_label,
            title="heatmap", palette=None, width=500,
            height=500,**kwargs):
    from bokeh.charts import HeatMap
    if not palette:
        from bokeh.palettes import RdBu11 as palette_tmpl
        palette = palette_tmpl
    hm = HeatMap(heatMapDF, x=xlabel, y=ylabel, values=value_label,
                        title=title, height=height, width=width, palette=palette, **kwargs)
    return hm

def scatterplot(scatterDF, xcol, ycol,
                xlabel=None, ylabel=None,
                group=None, plttitle=None, **kwargs):
    fig_kwargs = kwargs.get('figure')
    if fig_kwargs:
        p = figure(title=plttitle, **fig_kwargs)
    else:
        p = figure(title=plttitle)
    from bokeh.charts import Scatter

    if not xlabel:
        xlabel = xcol
    if not ylabel:
        ylabel = ycol

    if not group:
        p.circle(scatterDF[xcol], scatterDF[ycol], size=5, **kwargs)
    else:
        groups = list(scatterDf[group].unique())
        colors = genColors(len(groups))
        for group in groups:
            color = colors.pop()
            p.circle(scatterDf[xcol], scatterDf[ycol], size=5, color=color )
    p.xaxis.axis_label = str(xcol)
    p.yaxis.axis_label = str(ycol)
    return p

def pieChart(df, column, **kwargs):

    wedges = []
    wedge_sum = 0
    total = len(df)
    colors = genColors(df[column].nunique())
    for i, (key, val) in enumerate(df.groupby(column).size().iteritems()):
        wedge = dict()
        pct = val/float(total)
        wedge['start'] = 2 * PI * wedge_sum
        wedge_sum = (val/float(total)) + wedge_sum
        wedge['end'] = 2 * PI * wedge_sum
        wedge['name'] = '{}-{:.2f} %'.format(key, pct)
        wedge['color'] = colors.pop()
        wedges.append(wedge)
    p = figure(x_range=(-1,1), y_range=(-1,1), x_axis_label=column, **kwargs)

    for i, wedge in enumerate(wedges):
        p.wedge(x=0, y=0, radius=1, start_angle=wedge['start'], end_angle=wedge['end'],
                color=wedge['color'], legend=wedge['name'])
    return p

def mcircle(p, x, y, **kwargs):
    p.circle(x, y, **kwargs)

def mscatter(p, x, y, typestr="o"):
    p.scatter(x, y, marker=typestr, alpha=0.5)

def mtext(p, x, y, textstr, **kwargs):
   p.text(x, y, text=[textstr],
         text_color=kwargs.get('text_color'),
         text_align="center", text_font_size="10pt")

def boxplot(xrange, yrange, boxSource, xlabel='x', ylabel='y', colors=list()):
    p=figure(
        title='\"Party\" Disturbance Calls in LA',
        x_range=xrange,
        y_range=yrange)
        #tools=TOOLS)

    p.plot_width=900
    p.plot_height = 400
    p.toolbar_location='left'

    p.rect(xlabel, ylabel, 1, 1, source=boxSource, color=colors, line_color=None)

    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "10pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi/3

    return p

def sb_boxplot(dataframe, quant_field, cat_fields=None, facetCol=None ):
    assert quant_field
    if cat_fields:
        assert(len(cat_fields) <=2)
        #assert(all([isinstance(dataframe[field].dtype, str) for  field in cat_fields]))
    import seaborn as sns
    sns.set_style("whitegrid")
    tips = sns.load_dataset("tips")
    if not facetCol:
        if not cat_fields:
            ax = sns.boxplot(dataframe[quant_field])
        elif len(cat_fields)==1:
            sns.boxplot(x=cat_fields[0], y=quant_field, data=dataframe)
        else:
            sns.boxplot(x=cat_fields[0], y=quant_field,
                        hue=cat_fields[1], data=dataframe,
                        palette="Set3", linewidth=2.5)
    else:
        fg = sns.FacetGrid(dataframe, col=facetCol, size=4, aspect=7)
        (fg.map(sns.boxplot, cat_fields[0], quant_field,cat_fields[1])\
               .despine(left=True)\
               .add_legend(title=cat_fields[1]))

def sb_heatmap(df, label):
    # Creating heatmaps in matplotlib is more difficult than it should be.
    # Thankfully, Seaborn makes them easy for us.
    # http://stanford.edu/~mwaskom/software/seaborn/
    import seaborn as sns
    sns.set(style='white')
    sns.heatmap(df.T, mask=df.T.isnull(), annot=True, fmt='.0%');

def sb_piechart(df,column):
    pass

def sb_distplot(df, column):
    row = kwargs.get( 'row' , None )
    col = kwargs.get( 'col' , None )
    facet = sns.FacetGrid( df , hue=target , aspect=4 , row = row , col = col )
    facet.map( sns.kdeplot , column , shade= True )
    facet.set( xlim=( df[column] , df[column].max() ) )
    facet.add_legend()
    return to_bokeh(facet)

def sb_violinplot(series, dataframe=None, groupCol = None, **kwargs):
    import pandas as pd
    import seaborn as sns
    if not groupCol:
        assert isinstance(series, pd.Series)
        return to_bokeh(sns.violinplot(x=series, **kwargs).figure)
    else:
        assert dataframe and groupCol
        assert isinstance(series, str)
        return to_bokeh(sns.violinplot(x=groupCol, y=series, data=dataframe, **kwargs).figure)

def sb_jointplot(series1, series2):
    import numpy as np
    import seaborn as sns
    sns.set(style="white")

    # Generate a random correlated bivariate dataset
    #rs = np.random.RandomState(5)
    #mean = [0, 0]
    #cov = [(1, .5), (.5, 1)]
    #x1, x2 = rs.multivariate_normal(mean, cov, 500).T
    #x1 = pd.Series(x1, name="$X_1$")
    #x2 = pd.Series(x2, name="$X_2$")

    # Show the joint distribution using kernel density estimation
    sns.jointplot(series1, series2, kind="kde", size=7, space=0)

def gp_pointplot(geo_dataframe, geo_locations, scale_column):
    import geoplot.crs as gcrs
    import geoplot as gplt

    proj = gcrs.AlbersEqualArea()# central_longitude=-98, central_latitude=39.5)

    ax = gplt.polyplot(geo_locations,
                       projection=proj,
                       zorder=-1,
                       linewidth=0.5,
                        legend_kwargs={'frameon': False, 'loc': 'lower right'},
                       **kwargs
                       )
    gplt.pointplot(geo_dataframe,
                   scale=scale_column,
                   ax=ax,
                   projection=proj,
                   **kwargs
                   )
    pass

def gp_polyplot(geo_dataframe):
    import geoplot as gplt



