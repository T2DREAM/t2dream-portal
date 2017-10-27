import React from 'react';
import PropTypes from 'prop-types';
import _ from 'underscore';
import url from 'url';
import moment from 'moment';
import { FetchedData, FetchedItems, Param } from './fetched';
import { Panel, PanelBody } from '../libs/bootstrap/panel';
import DropdownButton from '../libs/bootstrap/button';
import { DropdownMenu } from '../libs/bootstrap/dropdown-menu';
import { FacetList, Listing } from './search';
import * as globals from './globals';

const newsUri = '/search/?type=Page&news=true&status=released';

// Convert the selected organisms and assays into an encoded query.
function generateQuery(selectedOrganisms, selectedAssayCategory) {
    // Make the base query.
    let query = selectedAssayCategory === 'COMPPRED' ? '?type=Annotation&encyclopedia_version=3' : '?type=Experiment&status=released';

    // Add the selected assay category, if any (doesn't apply to Computational Predictions).
    if (selectedAssayCategory && selectedAssayCategory !== 'COMPPRED') {
        query += `&assay_slims=${selectedAssayCategory}`;
    }

    // Add all the selected organisms, if any
    if (selectedOrganisms.length) {
        const organismSpec = selectedAssayCategory === 'COMPPRED' ? 'organism.scientific_name=' : 'replicates.library.biosample.donor.organism.scientific_name=';
        const queryStrings = {
            HUMAN: `${organismSpec}Homo+sapiens`, // human
        };
        const organismQueries = selectedOrganisms.map(organism => queryStrings[organism]);
        query += `&${organismQueries.join('&')}`;
    }

    return query;
}


// Main page component to render the home page
export default class Home extends React.Component {
    constructor(props) {
        super(props);

        // Set initial React state.
        this.state = {
            current: '?type=Experiment&status=released', // show all released experiments
            organisms: [], // create empty array of selected tabs
            assayCategory: '',
            socialHeight: 0,
        };

        // Required binding of `this` to component methods or else they can't see `this`.
        this.handleAssayCategoryClick = this.handleAssayCategoryClick.bind(this);
        this.handleTabClick = this.handleTabClick.bind(this);
        this.newsLoaded = this.newsLoaded.bind(this);
    }

    handleAssayCategoryClick(assayCategory) {
        if (this.state.assayCategory === assayCategory) {
            this.setState({ assayCategory: '' });
        } else {
            this.setState({ assayCategory: assayCategory });
        }
    }

    handleTabClick(selectedTab) {
        // Create a copy of this.state.newtabs so we can manipulate it in peace.
        const tempArray = _.clone(this.state.organisms);
        if (tempArray.indexOf(selectedTab) === -1) {
            // if tab isn't already in array, then add it
            tempArray.push(selectedTab);
        } else {
            // otherwise if it is in array, remove it from array and from link
            const indexToRemoveArray = tempArray.indexOf(selectedTab);
            tempArray.splice(indexToRemoveArray, 1);
        }

        // Update the list of user-selected organisms.
        this.setState({ organisms: tempArray });
    }

    // Called when the news content loads so that we can get its height. That lets us match up the
    // height of <TwitterWidget>. If we don't have any news items, nodeRef has `undefined` and we
    // just hard-code the height at 600 so that the Twitter widget has some space.
    newsLoaded(nodeRef) {
        this.setState({ socialHeight: nodeRef ? nodeRef.clientHeight : 600 });
    }

    render() {
        // Based on the currently selected organisms and assay category, generate a query string
        // for the GET request to retrieve chart data.
        const currentQuery = generateQuery(this.state.organisms, this.state.assayCategory);

        return (
            <div className="whole-page">
                <div className="row">
                    <div className="col-xs-12">
                        <Panel>
                            <AssayClicking assayCategory={this.state.assayCategory} handleAssayCategoryClick={this.handleAssayCategoryClick} />
                            <div className="graphs">
                                <div className="row">
                                    <HomepageChartLoader organisms={this.state.organisms} assayCategory={this.state.assayCategory} query={currentQuery} />
                                </div>
                            </div>
                            
                                 <div className="social">
                                <div className="social-news">
                                  <div className="news-header">
                                        <h3>News <a href="/news/" title="T2DREAM news" className="search-ref">View all news...</a></h3>
                                    </div>
                                    <NewsLoader newsLoaded={this.newsLoaded} />

                                </div>
                                     
                            </div>
                        </Panel>
                    </div>
                </div>
            </div>
        );
    }
}


// Given retrieved data, draw all home-page charts.
const ChartGallery = props => (
    <PanelBody>
    
    </PanelBody>
);

ChartGallery.propTypes = {
    query: PropTypes.string, // Query string to add to /matrix/ URI
};


// Component to allow clicking boxes on classic image
class AssayClicking extends React.Component {
    constructor(props) {
        super(props);

        // Required binding of `this` to component methods or else they can't see `this`.
        this.sortByAssay = this.sortByAssay.bind(this);
    }

    // Properly adds or removes assay category from link
    sortByAssay(category, e) {
        function handleClick(cat, ctx) {
            // Call the Home component's function to record the new assay cateogry
            ctx.props.handleAssayCategoryClick(cat); // handles assay category click
        }

        if (e.type === 'touchend') {
            handleClick(category, this);
            this.assayClickHandled = true;
        } else if (e.type === 'click' && !this.assayClickHandled) {
            handleClick(category, this);
        } else {
            this.assayClickHandled = false;
        }
    }

    // Renders classic image and svg rectangles
    render() {
        const assayList = [
            '3D+chromatin+structure',
            'DNA+accessibility',
            'DNA+binding',
            'DNA+methylation',
            'COMPPRED',
            'Transcription',
            'RNA+binding',
        ];
        const assayCategory = this.props.assayCategory;

        return (
            <div ref="graphdisplay">
                <div className="overall-classic">
                 <div className="site-banner">
                  <div className="site-banner-intro">
		  <div className="site-banner-header">
		  <img src="/static/img/logo.png" alt="logo"/>
                   <h1>T2DREAM</h1>
                  </div> 
		  <div className= "site-banner-title">
		        <p></p>
		         <h4>Type 2 Diabetes Regulatory Annotation Map</h4> 
		 </div>
                            <div className="site-banner-intro-content">
				<p>The T2DREAM project collects and provides data on the human genome and epigenome to facilitate genetic studies of type 2 diabetes and its complications.  This resource is a component of the AMP T2D consortium, which includes the National Institute for Diabetes and Digestive and Kidney Diseases (NIDDK) and an international collaboration of researchers.</p>
                            </div>
                        </div>
		       <div className="site-banner-search">
		       
                                      <h4 className="search-header">Explore experiments: </h4>
                                      <SearchEngine />
                                      <h4 className="search-header">Explore annotations:</h4>
                                      <SearchEngine1 />
                                      <AdvSearch />
		       </div>
                    </div>
            </div>
            </div>
        );
    }
}

AssayClicking.propTypes = {
    assayCategory: PropTypes.string.isRequired, // Test to display in each audit's detail, possibly containing @ids that this component turns into links automatically
};


// Draw an overlay button on the ENCODE banner.
const BannerOverlayButton = (props) => {
    const { item, x, y, width, height, selected, clickHandler } = props;

    return (
        <rect
            id={item}
            x={x}
            y={y}
            width={width}
            height={height}
            className={`rectangle-box${selected ? ' selected' : ''}`}
            onClick={(e) => { clickHandler(item, e); }}
        />
    );
};

BannerOverlayButton.propTypes = {
    item: PropTypes.string, // ID of button being clicked
    x: PropTypes.string, // X coordinate of button
    y: PropTypes.string, // Y coordinate of button
    width: PropTypes.string, // Width of button in pixels
    height: PropTypes.string, // Height of button in pixels
    selected: PropTypes.bool, // `true` if button is selected
    clickHandler: PropTypes.func, // Function to call when the button is clicked
};


// Passes in tab to handleTabClick
class TabClicking extends React.Component {
    render() {
        const { organisms, handleTabClick } = this.props;
        return (
            <div ref="tabdisplay">
                <div className="organism-selector">
                    <OrganismSelector organism="Human" selected={organisms.indexOf('HUMAN') !== -1} clickHandler={handleTabClick} />
                </div>
            </div>
        );
    }
}

TabClicking.propTypes = {
    organisms: PropTypes.array, // Array of currently selected tabs
    handleTabClick: PropTypes.func, // Function to call when a tab is clicked
};


const OrganismSelector = (props) => {
    const { organism, selected, clickHandler } = props;

    return (
        <button className={`organism-selector__tab${selected ? ' organism-selector--selected' : ''}`} onClick={() => { clickHandler(organism.toUpperCase(organism)); }}>
            {organism}
        </button>
    );
};

OrganismSelector.propTypes = {
    organism: PropTypes.string, // Organism this selector represents
    selected: PropTypes.bool, // `true` if selector is selected
    clickHandler: PropTypes.func, // Function to call to handle a selector click
};


// Initiates the GET request to search for experiments, and then pass the data to the HomepageChart
// component to draw the resulting chart.
const HomepageChartLoader = (props) => {
    const { query, organisms, assayCategory } = props;

    return (
        <FetchedData ignoreErrors>
            <Param name="data" url={`/search/${query}`} />
            <ChartGallery organisms={organisms} assayCategory={assayCategory} query={query} />
        </FetchedData>
    );
};

HomepageChartLoader.propTypes = {
    query: PropTypes.string, // Current search URI based on selected assayCategory
    organisms: PropTypes.array, // Array of selected organism strings
    assayCategory: PropTypes.string, // Selected assay category
};


// Draw the total chart count in the middle of the donut.
function drawDonutCenter(chart) {
    const canvasId = chart.chart.canvas.id;
    const width = chart.chart.width;
    const height = chart.chart.height;
    const ctx = chart.chart.ctx;

    ctx.fillStyle = '#000000';
    ctx.restore();
    const fontSize = (height / 114).toFixed(2);
    ctx.font = `${fontSize}em sans-serif`;
    ctx.textBaseline = 'middle';

    if (canvasId === 'myChart' || canvasId === 'myChart2') {
        const data = chart.data.datasets[0].data;
        const total = data.reduce((prev, curr) => prev + curr);
        const textX = Math.round((width - ctx.measureText(total).width) / 2);
        const textY = height / 2;

        ctx.clearRect(0, 0, width, height);
        ctx.fillText(total, textX, textY);
        ctx.save();
    } else {
        ctx.clearRect(0, 0, width, height);
    }
}


// Component to display the D3-based chart for Project
class HomepageChart extends React.Component {
    constructor(props) {
        super(props);
        this.wrapperHeight = 200;
        this.createChart = this.createChart.bind(this);
        this.updateChart = this.updateChart.bind(this);
    }

    componentDidMount() {
        // Create the chart, and assign the chart to this.myPieChart when the process finishes.
        if (document.getElementById('myChart')) {
            this.createChart(this.facetData);
        }
    }

    componentDidUpdate() {
        if (this.myPieChart) {
            // Existing data updated
            this.updateChart(this.myPieChart, this.facetData);
        } else if (this.facetData.length) {
            // Chart existed but was destroyed for lack of data. Rebuild the chart.
            this.createChart(this.facetData);
        }
    }

    // Draw the Project chart, for initial load, or when the previous load had no data for this
    // chart.
    createChart(facetData) {
        require.ensure(['chart.js'], (require) => {
            const Chart = require('chart.js');

            // for each item, set doc count, add to total doc count, add proper label, and assign color.
            const colors = this.context.projectColors.colorList(facetData.map(term => term.key), { shade: 10 });
            const data = [];
            const labels = [];

            // Convert facet data to chart data.
            facetData.forEach((term, i) => {
                data[i] = term.doc_count;
                labels[i] = term.key;
            });

            // adding total doc count to middle of donut
            // http://stackoverflow.com/questions/20966817/how-to-add-text-inside-the-doughnut-chart-using-chart-js/24671908
            Chart.pluginService.register({
                beforeDraw: drawDonutCenter,
            });

            // Pass the assay_title counts to the charting library to render it.
            const canvas = document.getElementById('myChart');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                this.myPieChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: colors,
                        }],
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false, // Hide automatically generated legend; we draw it ourselves
                        },
                        animation: {
                            duration: 200,
                        },
                        legendCallback: (chart) => { // allows for legend clicking
                            const chartData = chart.data.datasets[0].data;
                            const text = [];
                            text.push('<ul>');
                            for (let i = 0; i < chartData.length; i += 1) {
                                if (chartData[i]) {
                                    text.push('<li>');
                                    text.push(`<a href="/matrix/${this.props.query}&award.project=${chart.data.labels[i]}">`); // go to matrix view when clicked
                                    text.push(`<span class="chart-legend-chip" style="background-color:${chart.data.datasets[0].backgroundColor[i]}"></span>`);
                                    if (chart.data.labels[i]) {
                                        text.push(`<span class="chart-legend-label">${chart.data.labels[i]}</span>`);
                                    }
                                    text.push('</a></li>');
                                }
                            }
                            text.push('</ul>');
                            return text.join('');
                        },
                        onClick: (e) => {
                            // React to clicks on pie sections
                            const activePoints = this.myPieChart.getElementAtEvent(e);

                            if (activePoints[0]) { // if click on wrong area, do nothing
                                const clickedElementIndex = activePoints[0]._index;
                                const term = this.myPieChart.data.labels[clickedElementIndex];
                                this.context.navigate(`/matrix/${this.props.query}&award.project=${term}`);
                            }
                        },
                    },
                });

                // Have chartjs draw the legend into the DOM.
                document.getElementById('chart-legend').innerHTML = this.myPieChart.generateLegend();

                // Save the chart <div> height so we can set it to that value when no data's available.
                const chartWrapperDiv = document.getElementById('chart-wrapper-1');
                this.wrapperHeight = chartWrapperDiv.clientHeight;
            }
        });
    }

    // Update existing chart with new data.
    updateChart(Chart, facetData) {
        // for each item, set doc count, add to total doc count, add proper label, and assign color.
        const colors = this.context.projectColors.colorList(facetData.map(term => term.key), { shade: 10 });
        const data = [];
        const labels = [];

        // Convert facet data to chart data.
        facetData.forEach((term, i) => {
            data[i] = term.doc_count;
            labels[i] = term.key;
        });

        // Update chart data and redraw with the new data
        Chart.data.datasets[0].data = data;
        Chart.data.datasets[0].backgroundColor = colors;
        Chart.data.labels = labels;
        Chart.update();

        // Redraw the updated legend
        document.getElementById('chart-legend').innerHTML = Chart.generateLegend();
    }

    render() {
        const facets = this.props.data && this.props.data.facets;
        let total;

        // Get all project facets, or an empty array if none.
        if (facets) {
            const projectFacet = facets.find(facet => facet.field === 'award.project');
            this.facetData = projectFacet ? projectFacet.terms : [];
            const docCounts = this.facetData.length ? this.facetData.map(data => data.doc_count) : [];
            total = docCounts.length ? docCounts.reduce((prev, curr) => prev + curr) : 0;

            // No data with the current selection, but we used to? Destroy the existing chart so we can
            // display a no-data message instead.
            if ((this.facetData.length === 0 || total === 0) && this.myPieChart) {
                this.myPieChart.destroy();
                this.myPieChart = null;
            }
        } else {
            this.facets = null;
            if (this.myPieChart) {
                this.myPieChart.destroy();
                this.myPiechart = null;
            }
        }

        return (
            <div>
                <div className="title">
                    Project
                    <center><hr width="80%" color="blue" /></center>
                </div>
                {this.facetData.length && total ?
                    <div id="chart-wrapper-1" className="chart-wrapper">
                        <div className="chart-container">
                            <canvas id="myChart" />
                        </div>
                        <div id="chart-legend" className="chart-legend" />
                    </div>
                    :
                    <div className="chart-no-data" style={{ height: this.wrapperHeight }}><p>No data to display</p></div>
                }
            </div>
        );
    }
}

HomepageChart.propTypes = {
    query: PropTypes.string,
    data: PropTypes.object,
};

HomepageChart.contextTypes = {
    navigate: PropTypes.func,
    projectColors: PropTypes.object, // DataColor instance for experiment project
};


// Component to display the D3-based chart for Biosample
class HomepageChart2 extends React.Component {
    constructor(props) {
        super(props);
        this.wrapperHeight = 200;
        this.createChart = this.createChart.bind(this);
        this.updateChart = this.updateChart.bind(this);
    }

    componentDidMount() {
        if (document.getElementById('myChart2')) {
            this.createChart(this.facetData);
        }
    }

    componentDidUpdate() {
        if (this.myPieChart) {
            // Existing data updated
            this.updateChart(this.myPieChart, this.facetData);
        } else if (this.facetData.length) {
            // Chart existed but was destroyed for lack of data. Rebuild the chart.
            this.createChart(this.facetData);
        }
    }

    createChart(facetData) {
        // Draw the chart of search results given in this.props.data.facets. Since D3 doesn't work
        // with the React virtual DOM, we have to load it separately using the webpack .ensure
        // mechanism. Once the callback is called, it's loaded and can be referenced through
        // require.
        require.ensure(['chart.js'], (require) => {
            const Chart = require('chart.js');
            const colors = this.context.biosampleTypeColors.colorList(facetData.map(term => term.key), { shade: 10 });
            const data = [];
            const labels = [];

            facetData.forEach((term, i) => {
                data[i] = term.doc_count;
                labels[i] = term.key;
            });

            // adding total doc count to middle of donut
            // http://stackoverflow.com/questions/20966817/how-to-add-text-inside-the-doughnut-chart-using-chart-js/24671908
            Chart.pluginService.register({
                beforeDraw: drawDonutCenter,
            });

            // Pass the assay_title counts to the charting library to render it.
            const canvas = document.getElementById('myChart2');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                this.myPieChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: colors,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false, // hiding automatically generated legend
                        },
                        animation: {
                            duration: 200,
                        },
                        legendCallback: (chart) => { // allows for legend clicking
                            const chartData = chart.data.datasets[0].data;
                            const text = [];
                            text.push('<ul>');
                            for (let i = 0; i < chartData.length; i += 1) {
                                if (chartData[i]) {
                                    text.push('<li>');
                                    text.push(`<a href="/matrix/${this.props.query}&biosample_type=${chart.data.labels[i]}">`); // go to matrix view when clicked
                                    text.push(`<span class="chart-legend-chip" style="background-color:${chart.data.datasets[0].backgroundColor[i]}"></span>`);
                                    if (chart.data.labels[i]) {
                                        text.push(`<span class="chart-legend-label">${chart.data.labels[i]}</span>`);
                                    }
                                    text.push('</a></li>');
                                }
                            }
                            text.push('</ul>');
                            return text.join('');
                        },
                        onClick: (e) => {
                            // React to clicks on pie sections
                            const query = this.computationalPredictions ? 'biosample_type=' : 'replicates.library.biosample.biosample_type=';
                            const activePoints = this.myPieChart.getElementAtEvent(e);
                            if (activePoints[0]) {
                                const clickedElementIndex = activePoints[0]._index;
                                const term = this.myPieChart.data.labels[clickedElementIndex];
                                this.context.navigate(`/matrix/${this.props.query}&${query}${term}`); // go to matrix view
                            }
                        },
                    },
                });
            } else {
                this.myPieChart = null;
            }

            // Have chartjs draw the legend into the DOM.
            const legendElement = document.getElementById('chart-legend-2');
            if (legendElement) {
                legendElement.innerHTML = this.myPieChart.generateLegend();
            }

            // Save the chart <div> height so we can set it to that value when no data's available.
            const chartWrapperDiv = document.getElementById('chart-wrapper-2');
            if (chartWrapperDiv) {
                this.wrapperHeight = chartWrapperDiv.clientHeight;
            }
        });
    }

    updateChart(Chart, facetData) {
        // for each item, set doc count, add to total doc count, add proper label, and assign color.
        const colors = this.context.biosampleTypeColors.colorList(facetData.map(term => term.key), { shade: 10 });
        const data = [];
        const labels = [];

        // Convert facet data to chart data.
        facetData.forEach((term, i) => {
            data[i] = term.doc_count;
            labels[i] = term.key;
        });

        // Update chart data and redraw with the new data
        Chart.data.datasets[0].data = data;
        Chart.data.datasets[0].backgroundColor = colors;
        Chart.data.labels = labels;
        Chart.update();

        // Redraw the updated legend
        document.getElementById('chart-legend-2').innerHTML = Chart.generateLegend(); // generates legend
    }

    render() {
        const facets = this.props.data && this.props.data.facets;
        let total;

        // Our data source will be different for computational predictions
        if (facets) {
            this.computationalPredictions = this.props.assayCategory === 'COMPPRED';
            const assayFacet = facets.find(facet => facet.field === 'biosample_type');
            this.facetData = assayFacet ? assayFacet.terms : [];
            const docCounts = this.facetData.length ? this.facetData.map(data => data.doc_count) : [];
            total = docCounts.length ? docCounts.reduce((prev, curr) => prev + curr) : 0;

            // No data with the current selection, but we used to destroy the existing chart so we can
            // display a no-data message instead.
            if ((this.facetData.length === 0 || total === 0) && this.myPieChart) {
                this.myPieChart.destroy();
                this.myPieChart = null;
            }
        } else {
            this.facets = null;
            if (this.myPieChart) {
                this.myPieChart.destroy();
                this.myPiechart = null;
            }
        }

        return (
            <div>
                <div className="title">
                    Biosample Type
                    <center><hr width="80%" color="blue" /></center>
                </div>
                {this.facetData.length && total ?
                    <div id="chart-wrapper-2" className="chart-wrapper">
                        <div className="chart-container">
                            <canvas id="myChart2" />
                        </div>
                        <div id="chart-legend-2" className="chart-legend" />
                    </div>
                    :
                    <div className="chart-no-data" style={{ height: this.wrapperHeight }}>No data to display</div>
                }
            </div>
        );
    }
}

HomepageChart2.propTypes = {
    query: PropTypes.string,
    data: PropTypes.object,
    assayCategory: PropTypes.string,
};

HomepageChart2.contextTypes = {
    navigate: PropTypes.func,
    biosampleTypeColors: PropTypes.object, // DataColor instance for experiment project
};


// Draw the small triangle above the selected assay in the "Assay Categories" chart if the user has
// selected an assay from the classic image.
function drawColumnSelects(currentAssay, ctx, data) {
    // Adapted from https://github.com/chartjs/Chart.js/issues/2477#issuecomment-255042267
    if (currentAssay) {
        ctx.fillStyle = '#2138B2';

        // Find the data with a label matching the currently selected assay.
        const currentColumn = data.labels.indexOf(currentAssay);
        if (currentColumn !== -1) {
            // Get information on the matching column's coordinates so we know where to draw the
            // triangle.
            const dataset = data.datasets[0];
            const model = dataset._meta[Object.keys(dataset._meta)[0]].data[currentColumn]._model;

            // Draw the triangle into the HTML5 <canvas> element.
            ctx.beginPath();
            ctx.moveTo(model.x - 5, model.y - 8);
            ctx.lineTo(model.x, model.y - 3);
            ctx.lineTo(model.x + 5, model.y - 8);
            ctx.fill();
        }
    }
}


// Component to display the D3-based chart for Biosample
class HomepageChart3 extends React.Component {
    constructor(props) {
        super(props);
        this.wrapperHeight = 200;
        this.createChart = this.createChart.bind(this);
        this.updateChart = this.updateChart.bind(this);
    }

    componentDidMount() {
        if (document.getElementById('myChart3')) {
            this.createChart(this.facetData);
        }
    }

    componentDidUpdate() {
        if (this.myPieChart) {
            // Existing data updated
            this.updateChart(this.myPieChart, this.facetData);
        } else if (this.facetData.length) {
            // Chart existed but was destroyed for lack of data. Rebuild the chart.
            this.createChart(this.facetData);
        }
    }

    createChart(facetData) {
        // Draw the chart of search results given in this.props.data.facets. Since D3 doesn't work
        // with the React virtual DOM, we have to load it separately using the webpack .ensure
        // mechanism. Once the callback is called, it's loaded and can be referenced through
        // require.
        require.ensure(['chart.js'], (require) => {
            const Chart = require('chart.js');
            const colors = [];
            const data = [];
            const labels = [];
            const selectedAssay = (this.props.assayCategory && this.props.assayCategory !== 'COMPPRED') ? this.props.assayCategory.replace(/\+/g, ' ') : '';

            // For each item, set doc count, add to total doc count, add proper label, and assign
            // color.
            facetData.forEach((term, i) => {
                data[i] = term.doc_count;
                labels[i] = term.key;
                colors[i] = selectedAssay ? (term.key === selectedAssay ? 'rgb(255,217,98)' : 'rgba(255,217,98,.4)') : '#FFD962';
            });

            // Pass the counts to the charting library to render it.
            const canvas = document.getElementById('myChart3');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                this.myPieChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels, // full labels
                        datasets: [{
                            data: data,
                            backgroundColor: colors,
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false, // hiding automatically generated legend
                        },
                        hover: {
                            mode: false,
                        },
                        animation: {
                            duration: 0,
                            onProgress: function () { drawColumnSelects(selectedAssay, this.chart.ctx, this.data); },
                            onComplete: function () { drawColumnSelects(selectedAssay, this.chart.ctx, this.data); },
                        },
                        scales: {
                            xAxes: [{
                                gridLines: {
                                    display: false,
                                },
                                ticks: {
                                    autoSkip: false,
                                },
                            }],
                        },
                        layout: {
                            padding: {
                                top: 10,
                            },
                        },
                        onClick: (e) => {
                            // React to clicks on pie sections
                            const query = 'assay_slims=';
                            const activePoints = this.myPieChart.getElementAtEvent(e);
                            if (activePoints[0]) {
                                const clickedElementIndex = activePoints[0]._index;
                                const term = this.myPieChart.data.labels[clickedElementIndex];
                                this.context.navigate(`/matrix/${this.props.query}&${query}${term}`); // go to matrix view
                            }
                        },
                    },
                });

                // Save height of wrapper div.
                const chartWrapperDiv = document.getElementById('chart-wrapper-3');
                this.wrapperHeight = chartWrapperDiv.clientHeight;
            }
        });
    }

    updateChart(Chart, facetData) {
        // for each item, set doc count, add to total doc count, add proper label, and assign color.
        const data = [];
        const labels = [];
        const colors = [];

        // Convert facet data to chart data.
        const selectedAssay = (this.props.assayCategory && this.props.assayCategory !== 'COMPPRED') ? this.props.assayCategory.replace(/\+/g, ' ') : '';
        facetData.forEach((term, i) => {
            data[i] = term.doc_count;
            labels[i] = term.key;
            colors[i] = selectedAssay ? (term.key === selectedAssay ? 'rgb(255,217,98)' : 'rgba(255,217,98,.4)') : '#FFD962';
        });

        // Update chart data and redraw with the new data
        Chart.data.datasets[0].data = data;
        Chart.data.labels = labels;
        Chart.data.datasets[0].backgroundColor = colors;
        Chart.options.hover.mode = false;
        Chart.options.animation.onProgress = function () { drawColumnSelects(selectedAssay, this.chart.ctx, this.data); };
        Chart.options.animation.onComplete = function () { drawColumnSelects(selectedAssay, this.chart.ctx, this.data); };
        Chart.update();
    }

    render() {
        const facets = this.props.data && this.props.data.facets;
        let total;

        // Get all assay category facets, or an empty array if none
        if (facets) {
            const projectFacet = facets.find(facet => facet.field === 'assay_slims');
            this.facetData = projectFacet ? projectFacet.terms : [];
            const docCounts = this.facetData.length ? this.facetData.map(data => data.doc_count) : [];
            total = docCounts.length ? docCounts.reduce((prev, curr) => prev + curr) : 0;

            // No data with the current selection, but we used to? Destroy the existing chart so we can
            // display a no-data message instead.
            if ((this.facetData.length === 0 || total === 0) && this.myPieChart) {
                this.myPieChart.destroy();
                this.myPieChart = null;
            }
        } else {
            this.facets = null;
            if (this.myPieChart) {
                this.myPieChart.destroy();
                this.myPiechart = null;
            }
        }

        return (
            <div>
                <div className="title">
                    Assay Categories
                    <center><hr width="80%" color="blue" /></center>
                </div>
                {this.facetData.length && total ?
                    <div id="chart-wrapper-3" className="chart-wrapper">
                        <div className="chart-container-assaycat">
                            <canvas id="myChart3" />
                        </div>
                    </div>
                    :
                    <div className="chart-no-data" style={{ height: this.wrapperHeight }}>No data to display</div>
                }
            </div>
        );
    }
}

HomepageChart3.propTypes = {
    assayCategory: PropTypes.string,
    query: PropTypes.string,
    data: PropTypes.object,
};

HomepageChart3.contextTypes = {
    navigate: PropTypes.func,
};


// Render the most recent five news posts
class News extends React.Component {
    componentDidMount() {
        this.props.newsLoaded(this.nodeRef);
    }

    render() {
        const { items, nodeRef } = this.props;
        if (items && items.length) {
            return (
                <div ref={(node) => { this.nodeRef = node; }} className="news-listing">
                    {items.map(item =>
                        <div key={item['@id']} className="news-listing-item">
                            <h3>{item.title}</h3>
                            <h4>{moment.utc(item.date_created).format('MMMM D, YYYY')}</h4>
                            <div className="news-excerpt">{item.news_excerpt}</div>
                            <div className="news-listing-readmore">
                                <a href={item['@id']} title={`View news post for ${item.title}`} key={item['@id']}>Read more</a>
                            </div>
                        </div>,
                    )}
                </div>
            );
        }
        return <div className="news-empty">No news available at this time</div>;
    }
}

News.propTypes = {
    items: PropTypes.array,
    newsLoaded: PropTypes.func.isRequired, // Called parent once the news is loaded
    nodeRef: PropTypes.func, // React ref callback so we can get the news-listing DOM element in a higher component
};


// Send a GET request for the most recent five news posts. Don't make this a stateless component
// because we attach `ref` to this, and stateless components don't support that.
class NewsLoader extends React.Component {
    render() {
        return <FetchedItems {...this.props} url={`${newsUri}&limit=3`} Component={News} ignoreErrors newsLoaded={this.props.newsLoaded} />;
    }
}

NewsLoader.propTypes = {
    newsLoaded: PropTypes.func.isRequired, // Called parent once the news is loaded
};
class SearchEngine extends React.Component {
render()
{
return <Search />
}
}

SearchEngine.contextTypes = {
    location_href: PropTypes.string,
};

const Search = (props, context) => {
    const id = url.parse(context.location_href, true);
    const searchTerm = id.query.searchTerm || '';
    return (
        <form className="home-form" action="/search/">
            <div className="search-wrapper">
                <span>
                <input type="hidden" name="type" value="Experiment" />
                <input
                    className="form-control search-query"
                    id="home-search"
                    type="text"
                    placeholder="Enter search (e.g., islets, ATAC-seq)"
                    name="searchTerm"
                    defaultValue={searchTerm}
                    key={searchTerm}
                />
            <input type="submit" value="GO" className="submit_3 pull-right" />
            </span>
            </div>
        </form>
    );
};

Search.contextTypes = {
    location_href: PropTypes.string,
};

class SearchEngine1 extends React.Component {
render()
{
return <Search1 />
}
}

SearchEngine1.contextTypes = {
    location_href: PropTypes.string,
};

const Search1 = (props, context) => {
    const id1 = url.parse(context.location_href, true);
    const searchTerm1 = id1.query.searchTerm || '';
    return (
        <form className="home-form" action="/search/">
            <div className="search-wrapper">
                <span>
                <input type="hidden" name="type" value="Annotation" />
                <input
                    className="form-control search-query"
                    id="home-search"
                    type="text"
                    placeholder="Enter search (e.g., adipose, chromatin state)"
                    name="searchTerm"
                    defaultValue={searchTerm1}
                    key={searchTerm1}
                />
            <input type="submit" value="GO" className="submit_3 pull-right" />
            </span>
            </div>
        </form>
    );
};

Search1.contextTypes = {
    location_href: PropTypes.string,
};

const regionGenomes = [
    { value: 'GRCh37', display: 'hg19' },
    { value: 'GRCh38', display: 'GRCh38' },
    { value: 'GRCm37', display: 'mm9' },
    { value: 'GRCm38', display: 'mm10' },
];

const AutocompleteBox = (props) => {
    const terms = props.auto['@graph']; // List of matching terms from server                                                                                                                                                                                                 
    const handleClick = props.handleClick;
    const userTerm = props.userTerm && props.userTerm.toLowerCase(); // Term user entered                                                                                                                                                                                     

    if (!props.hide && userTerm && userTerm.length && terms && terms.length) {
        return (
            <ul className="adv-search-autocomplete">
                {terms.map((term) => {
                    let matchEnd;
                    let preText;
                    let matchText;
                    let postText;

                    // Boldface matching part of term                                                                                                                                                                                                                         
                    const matchStart = term.text.toLowerCase().indexOf(userTerm);
                    if (matchStart >= 0) {
                        matchEnd = matchStart + userTerm.length;
                        preText = term.text.substring(0, matchStart);
                        matchText = term.text.substring(matchStart, matchEnd);
                        postText = term.text.substring(matchEnd);
                    } else {
                        preText = term.text;
                    }
                    return (
                        <AutocompleteBoxMenu
                            key={term.text}
                            handleClick={handleClick}
                            term={term}
                            name={props.name}
                            preText={preText}
                            matchText={matchText}
                            postText={postText}
                        />
                    );
                }, this)}
            </ul>
        );
    }

    return null;
};

AutocompleteBox.propTypes = {
    auto: PropTypes.object,
    userTerm: PropTypes.string,
    handleClick: PropTypes.func,
    hide: PropTypes.bool,
    name: PropTypes.string,
};

AutocompleteBox.defaultProps = {
    auto: {}, // Looks required, but because it's built from <Param>, it can fail type checks.                                                                                                                                                                                
    userTerm: '',
    handleClick: null,
    hide: false,
    name: '',
};

// Draw the autocomplete box drop-down menu.                                                                                                                                                                                                                                  
class AutocompleteBoxMenu extends React.Component {
    constructor() {
        super();

        // Bind this to non-React methods.                                                                                                                                                                                                                                    
        this.handleClick = this.handleClick.bind(this);
    }

    // Handle clicks in the drop-down menu. It just calls the parent's handleClick function, giving                                                                                                                                                                           
    // it the parameters of the clicked item.                                                                                                                                                                                                                                 
    handleClick() {
        const { term, name } = this.props;
        this.props.handleClick(term.text, term.payload.id, name);
    }

    render() {
        const { preText, matchText, postText } = this.props;

        return (
            <li tabIndex="0" onClick={this.handleClick}>
                {preText}<b>{matchText}</b>{postText}
            </li>
        );
    }
}
AutocompleteBoxMenu.propTypes = {
    handleClick: PropTypes.func.isRequired, // Parent function to handle a click in a drop-down menu item                                                                                                                                                                     
    term: PropTypes.object.isRequired, // Object for the term being searched                                                                                                                                                                                                  
    name: PropTypes.string,
    preText: PropTypes.string, // Text before the matched term in the entered string                                                                                                                                                                                          
    matchText: PropTypes.string, // Matching text in the entered string                                                                                                                                                                                                       
    postText: PropTypes.string, // Text after the matched term in the entered string                                                                                                                                                                                          
};

AutocompleteBoxMenu.defaultProps = {
    name: '',
    preText: '',
    matchText: '',
    postText: '',
};

class AdvSearch extends React.Component {
    constructor() {
        super();

        // Set intial React state.                                                                                                                                                                                                                                            
        this.state = {
            disclosed: false,
            showAutoSuggest: false,
            searchTerm: '',
            coordinates: '',
            genome: regionGenomes[0].value,
            terms: {},
        };

        // Bind this to non-React methods.                                                                                                                                                                                                                                    
        this.handleDiscloseClick = this.handleDiscloseClick.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.handleAutocompleteClick = this.handleAutocompleteClick.bind(this);
        this.handleAssemblySelect = this.handleAssemblySelect.bind(this);
        this.tick = this.tick.bind(this);
    }

    componentDidMount() {
        // Use timer to limit to one request per second                                                                                                                                                                                                                       
        this.timer = setInterval(this.tick, 1000);
    }

    componentWillUnmount() {
        clearInterval(this.timer);
    }

    handleDiscloseClick() {
        this.setState(prevState => ({
            disclosed: !prevState.disclosed,
        }));
    }

    handleChange(e) {
        this.setState({ showAutoSuggest: true, terms: {} });
	this.newSearchTerm = e.target.value;
    }

    handleAutocompleteClick(term, id, name) {
        const newTerms = {};
        const inputNode = this.annotation;
        inputNode.value = term;
        newTerms[name] = id;
        this.setState({ terms: newTerms, showAutoSuggest: false });
        inputNode.focus();
        // Now let the timer update the terms state when it gets around to it.                                                                                                                                                                                                
    }

    handleAssemblySelect(event) {
        // Handle click in assembly-selection <select>                                                                                                                                                                                                                        
        this.setState({ genome: event.target.value });
    }

    tick() {
        if (this.newSearchTerm !== this.state.searchTerm) {
            this.setState({ searchTerm: this.newSearchTerm });
        }
    }
    render() {
        const context = this.props.context;
        const id = url.parse(this.context.location_href, true);
        const region = id.query.region || '';

        return (
                    <form className="home-form" ref="adv-search" role="form" autoComplete="off" aria-labelledby="tab1" action="/region-search/">
                        <input type="hidden" name="annotation" value={this.state.terms.annotation} />

                              <div className="form-group">
                              <h4> Search variants and regions: </h4>
                               <div className="input-group input-group-region-input">
                                <input id="annotation" ref={(input) => { this.annotation = input; }} defaultValue={region} name="region" placeholder="Enter Search (e.g. rs7903146, TCF7L2)
" type="text" className="form-control" onChange={this.handleChange} />
                                {(this.state.showAutoSuggest && this.state.searchTerm) ?
                                    <FetchedData loadingComplete>
                                        <Param name="auto" url={`/suggest/?genome=${this.state.genome}&q=${this.state.searchTerm}`} type="json" />
                                        <AutocompleteBox name="annotation" userTerm={this.state.searchTerm} handleClick={this.handleAutocompleteClick} />
                                    </FetchedData>
                                : null}
                               <div className="input-group-addon input-group-select-addon">
                                    <select value={this.state.genome} name="genome" onChange={this.handleAssemblySelect}>
                                        {regionGenomes.map(genomeId =>
                                            <option key={genomeId.value} value={genomeId.value}>{genomeId.display}</option>
                                        )}
                                    </select>
                               </div>
                               <input type="submit" value="GO" className="submit_4 pull-right" />
                              </div>
                               </div>
                    </form>
        );
    }
}

AdvSearch.propTypes = {
    context: PropTypes.object.isRequired,
};

AdvSearch.contextTypes = {
    autocompleteTermChosen: PropTypes.bool,
    autocompleteHidden: PropTypes.bool,
    onAutocompleteHiddenChange: PropTypes.func,
    location_href: PropTypes.string,
};

AdvSearch.propTypes = {
    context: PropTypes.object.isRequired,
};

AdvSearch.contextTypes = {
    autocompleteTermChosen: PropTypes.bool,
    autocompleteHidden: PropTypes.bool,
    onAutocompleteHiddenChange: PropTypes.func,
    location_href: PropTypes.string,
};

class TwitterWidget extends React.Component {
    constructor(props) {
        super(props);
        this.initialized = false;
        this.injectTwitter = this.injectTwitter.bind(this);
    }

    componentDidMount() {
        if (!this.initialized && this.props.height) {
            this.injectTwitter();
        }
    }

    componentDidUpdate() {
        if (!this.initialized && this.props.height) {
            this.injectTwitter();
        }
    }

    injectTwitter() {
        if (!this.initialized) {
            const link = this.anchor;
            this.initialized = true;
            const js = document.createElement('script');
            js.id = 'twitter-wjs';
            js.src = '//platform.twitter.com/widgets.js';
            return link.parentNode.appendChild(js);
        }
        return null;
    }

    render() {
        return (
            <div ref="twitterwidget">
                <div className="twitter-header">
                    <h3>Twitter <a href="https://twitter.com/T2DREAM_AMP" title="T2DREAM Twitter page in a new window or tab" target="_blank" rel="noopener noreferrer"className="twitter-ref">@T2DREAM_AMP</a></h3>
                </div>
                {this.props.height ?
                    <a
                        ref={(anchor) => { this.anchor = anchor; }}
                        className="twitter-timeline"
                        href="https://twitter.com/T2DREAM_AMP" // from T2DREAM twitter
                        data-chrome="noheader"
                        data-screen-name="T2DREAM_AMP"
                        data-height={this.props.height.toString()} // height so it matches with rest of site
                    >
                        @T2DREAM_AMP
                    </a>
                : null}
            </div>
        );
    }
}

