import React from 'react';
import PropTypes from 'prop-types';
import { auditDecor } from './audit';
import * as globals from './globals';
import { Breadcrumbs } from './navigation';
import { DbxrefList } from './dbxref';
import { PickerActions } from './search';

// Display a consortium object.
const ConsortiumComponent = (props, reactContext) => {
    const context = props.context;
    const itemClass = globals.itemClass(context, 'view-item');

    // Set up breadcrumbs
    const categoryTerms = context.categories && context.categories.map(category => `categories=${category}`);
    const crumbs = [
        { id: 'Consortium' },
        {
            id: context.categories ? context.categories.join(' + ') : null,
            query: (categoryTerms && categoryTerms.join('&')),
            tip: context.categories && context.categories.join(' + ') },
    ];

    return (
        <div className={itemClass}>
            <Breadcrumbs root="/search/?type=Consortium" crumbs={crumbs} />
            <h2>{context.title}</h2>
            {props.auditIndicators(context.audit, 'publication-audit', { session: reactContext.session })}
            {props.auditDetail(context.audit, 'publication-audit', { session: reactContext.session, except: context['@id'] })}
            {context.start_date ? <div className="start-date"><b>Start Date:  </b>{context.start_date}</div> : null}
            {context.end_date ? <div className="start-date"><b>End Date:  </b>{context.end_date}</div> : null}
            {context.description || (context.datasets && context.datasets.length) || (context.grants && context.grants.length) || (context.labs && context.labs.length)?
                <div className="view-detail panel">
                    <Abstract {...props} />
                </div>
            : null}

            {context.consortium_tools && context.consortium_tools.length ?
                <div>
                    <h3>Related Tools</h3>
                    <div className="panel view-detail" data-test="supplementarydata">
                        {context.consortium_tools.map((data, i) => <ConsortiumTools data={data} key={i} />)}
                    </div>
                </div>
            : null}
        </div>
    );
};

ConsortiumComponent.propTypes = {
    context: PropTypes.object.isRequired,
    auditIndicators: PropTypes.func.isRequired, // Audit decorator function
    auditDetail: PropTypes.func.isRequired,
};

ConsortiumComponent.contextTypes = {
    session: PropTypes.object, // Login information from <App>
};

// Note that Consortium needs to be exported for Jest tests.
const Consortium = auditDecor(ConsortiumComponent);
export default Consortium;

globals.contentViews.register(Consortium, 'Consortium');



const Abstract = (props) => {
    const context = props.context;
    return (
        <dl className="key-value">
            {context.project ?
                <div data-test="abstract">
                    <dt>Name</dt>
                    <dd><a href={context.url}>{context.project}</a></dd>
                </div>
            : null}
            {context.description ?
                <div data-test="abstract">
                    <dt>Description</dt>
                    <dd>{context.description}</dd>
                </div>
            : null}

            {context.grants ?
                <div data-test="grants">
                    <dt>Consortium Grants</dt>
                    <dd>
                        {context.grants.map((grant, i) => (
                            <span key={i}>
                                {i > 0 ? ', ' : ''}
                                <a href={grant['@id']}>{grant.name}</a>
                            </span>
                        ))}
                    </dd>
                </div>
            : null}


            {context.labs ?
                <div data-test="labs">
                    <dt>Consortium labs</dt>
                    <dd>
                        {context.labs.map((labs, i) => (
                            <span key={i}>
                                {i > 0 ? ', ' : ''}
                                <a href={labs['@id']}>{labs.title}</a>
                            </span>
                        ))}
                    </dd>
                </div>
            : null}

            {context.datasets && context.datasets.length ?
                <div data-test="datasets">
                    <dt>Datasets</dt>
                    <dd>
                        {context.datasets.map((dataset, i) => (
                            <span key={i}>
                                {i > 0 ? ', ' : ''}
                                <a href={dataset['@id']}>{dataset.accession}</a>
                            </span>
                        ))}
                    </dd>
                </div>
            : null}
            {context.publications ?
                <div data-test="references">
                    <dt>Publications</dt>
                    <dd>
                        {context.publications.map((publications, i) => (
                            <span key={i}>
                                {i > 0 ? ', ' : ''}
                                <a href={publications['@id']}>{publications.title}</a>
                            </span>
                        ))}
                    </dd>
                </div>
            : null}
        </dl>
    );
};

Abstract.propTypes = {
    context: PropTypes.object.isRequired, // Abstract being displayed
};

// Component to display the D3-based chart for Biosample
class HomepageChart2 extends React.Component {
    constructor(props) {
        super(props);
        this.wrapperHeight = 100;
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
            const colors = this.context.assayTypeColors.colorList(facetData.map(term => term.key), { shade: 10 });
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
                                    text.push(`<a href="/matrix/${this.props.query}&assay_type=${chart.data.labels[i]}">`); // go to matrix view when clicked
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
                            const query = 'assay_type=';
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
            const assayFacet = facets.find(facet => facet.field === 'assay_type');
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
                    Assay Type
                    <center><hr width="80%" color="blue" /></center>
                </div>
                
                    <div id="chart-wrapper-2" className="chart-wrapper">
                        <div className="chart-container">
                            <canvas id="myChart2" />
                        </div>
                        <div id="chart-legend-2" className="chart-legend" />
                    </div>
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


const ConsortiumTools = (props) => {
    const data = props.data;
    return (
        <section className="supplementary-data">
            <dl className="key-value">
	    
                {data.url ?
                    <div data-test="url"  style= {{ 'align-items': 'center', 'margin-top': '15px', 'margin-left':'10%', 'margin-bottom': '15px'}}>
		        <dt>Available Tool</dt>
                        <dd><a className="btn-lg btn-tools" href={data.url}>{data.consortium_tool_type}</a></dd>
                    </div>
                : null}

            </dl>
        </section>
    );
};

ConsortiumTools.propTypes = {
    data: PropTypes.object.isRequired,
};


class ConsortiumToolsListing extends React.Component {
    constructor() {
        super();

        // Set initial React state.
        this.state = { excerptExpanded: false };

        // Bind this to non-React methods.
        this.handleClick = this.handleClick.bind(this);
    }

    handleClick() {
        this.setState(prevState => ({
            excerptExpanded: !prevState.excerptExpanded,
        }));
    }

    render() {
        const { data, id, index } = this.props;
        // Make unique ID for ARIA identification
        const nodeId = id.replace(/\//g, '') + index;

        return (
            <div className="list-supplementary">
                {data.consortium_tool_type ?
                    <div><strong>Available consortium tools: </strong>{data.consortium_tool_type}</div>
                : null}

                {data.url ?
                    <div><strong>URL: </strong><a href={data.url}>{data.url}</a></div>
                : null}
            </div>
        );
    }
}

ConsortiumToolsListing.propTypes = {
    context: PropTypes.object.isRequired,
    id: PropTypes.string.isRequired,
    index: PropTypes.number,
};

ConsortiumToolsListing.defaultProps = {
    index: 0,
};


const ListingComponent = (props, context) => {
    const result = props.context;

    return (
        <li>
            <div className="clearfix">
                <PickerActions {...props} />
                <div className="pull-right search-meta">
                    <p className="type meta-title">Consortium</p>
                    <p className="type meta-status">{` ${result.status}`}</p>
                    {props.auditIndicators(result.audit, result['@id'], { session: context.session, search: true })}
                </div>
                <div className="accession"><a href={result['@id']}>{result.title}</a></div>
                <div className="data-row">
                    {result.consortium_tools && result.consortium_tools.length ?
                        <div>
                            {result.consortium_tools.map((context, i) =>
                                <ConsortiumToolsListing context={context} id={result['@id']} index={i} key={i} />
                            )}
                        </div>
                    : null}
                </div>
            </div>
            {props.auditDetail(result.audit, result['@id'], { session: context.session, forcedEditLink: true })}
        </li>
    );
};

ListingComponent.propTypes = {
    context: PropTypes.object.isRequired,
    auditIndicators: PropTypes.func.isRequired, // Audit decorator function
    auditDetail: PropTypes.func.isRequired, // Audit decorator function
};

ListingComponent.contextTypes = {
    session: PropTypes.object, // Login information from <App>
};

const Listing = auditDecor(ListingComponent);

globals.listingViews.register(Listing, 'Consortium');
