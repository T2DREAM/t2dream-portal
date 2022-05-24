import React from 'react';
import PropTypes from 'prop-types';
import { auditDecor } from './audit';
import * as globals from './globals';
import { Breadcrumbs } from './navigation';
import { DbxrefList } from './dbxref';
import { PickerActions } from './search';
import { ConsortiumBadge } from './image';

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
            <ConsortiumBadge rfa={context.rfa} addClasses="badge-heading" />
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

            {context.publications && context.publications.length ?
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
