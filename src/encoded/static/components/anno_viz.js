import React from 'react';
import PropTypes from 'prop-types';
import createReactClass from 'create-react-class';
import _ from 'underscore';
import moment from 'moment';
import globals from './globals';
import { Panel, PanelHeading, TabPanel, TabPanelPane } from '../libs/bootstrap/panel';
import { Modal, ModalHeader, ModalBody, ModalFooter } from '../libs/bootstrap/modal';
import { auditDecor, auditsDisplayed, AuditIcon } from './audit';
import StatusLabel from './statuslabel';
import { requestFiles, DownloadableAccession, BrowserSelector } from './objectutils';
import { Graph, JsonGraph } from './graph';
import { qcModalContent, qcIdToDisplay } from './quality_metric';
import { softwareVersionList } from './software';
import { FetchedData, Param } from './fetched';
import { collapseIcon } from '../libs/svg-icons';
import { SortTablePanel, SortTable } from './sorttable';
var button = require('../libs/bootstrap/button');

export const FileGallery = createReactClass({
    propTypes: {
        context: PropTypes.object, // Dataset object whose annotations we're rendering
    },

    contextTypes: {
        session: PropTypes.object, // Login information
        location_href: PropTypes.string, // URL of this variant search page, including query string stuff
    },

    render: function () {
        const { context } = this.props;

        return (
            <FetchedData ignoreErrors>
		<Param name="schemas" url="/profiles/" />
                <FileGalleryRenderer context={context} session={this.context.session} />
            </FetchedData>
        );
    },
});


export function assembleGraph(context, session, infoNodeId, query, regions, viz) {

    // Create an empty graph architecture that we fill in next.
    const jsonGraph = new JsonGraph(context.accession);


    const queryNodeId = query;
    const queryNodeLabel = query;
    const fileCssClass = `pipeline-node-file${infoNodeId === queryNodeId ? ' active' : ''}`;
    jsonGraph.addNode(queryNodeId, queryNodeLabel, {
	cssClass: fileCssClass,
	type: 'Viz',
	shape: 'rect',
	cornerRadius: 16,
	});
    Object.keys(viz).forEach((vizId) => {
	const annotations = viz[vizId];
	const annotationNodeId = annotations['id'];
	const annotationNodeLabel = annotations['id'];
	const regionNodeId = annotations['value'];
	const regionNodeLabel = annotations['value'];
	jsonGraph.addNode(annotationNodeId, annotationNodeLabel, {
	    cssClass: fileCssClass,
	    type: 'Viz',
	    shape: 'rect',
	    cornerRadius: 16,
	    });
	jsonGraph.addNode(regionNodeId, regionNodeLabel, {
	    cssClass: fileCssClass,
	    type: 'Viz',
	    shape: 'rect',
	    cornerRadius: 16,
	    });
	jsonGraph.addEdge(queryNodeId, annotationNodeId);
	jsonGraph.addEdge(annotationNodeId, regionNodeId);
	});

    return { graph: jsonGraph };
}

// Function to render the variant annotation graph, and it gets called after the viz results i.e. annotation type, state and biosample 
const FileGalleryRenderer = createReactClass({
    propTypes: {
        context: PropTypes.object, // Dataset whose files we're rendering
        hideGraph: PropTypes.bool, // T to hide graph display
    },

    contextTypes: {
        session: PropTypes.object,
        session_properties: PropTypes.object,
        location_href: PropTypes.string,
    },
    
    getInitialState: function () {
        return {
            infoNodeId: '', // @id of node whose info panel is open
            infoModalOpen: false, // True if info modal is open
            relatedFiles: [],
        };
    },
    // Called from child components when the selected node changes.
    setInfoNodeId: function (nodeId) {
        this.setState({ infoNodeId: nodeId });
    },

    setInfoNodeVisible: function (visible) {
        this.setState({ infoNodeVisible: visible });
    },


    render: function () {
        const { context, schemas, hideGraph } = this.props;
        let jsonGraph;
     	const query = context['query'];
	const regions = context['regions'];
	const viz = context['viz'];
	const loggedIn = this.context.session && this.context.session['auth.userid'];

        // Build node graph of the files and analysis steps with this experiment
        if ( regions && regions.length ) {
	    const { graph } = assembleGraph(context, this.context.session, this.state.infoNodeId, query, regions, viz);
            jsonGraph = graph;
	    return (
            <Panel>
		{/* Display the strip of filgering controls */}
   	    
		{!hideGraph ?
		 <FileGraph
		 context={context}
		 items={regions}
		 graph={jsonGraph}
		 query={query}
		 viz={viz}
		 session={this.context.session}
		 infoNodeId={this.state.infoNodeId}
		 setInfoNodeId={this.setInfoNodeId}
		 infoNodeVisible={this.state.infoNodeVisible}
		 setInfoNodeVisible={this.setInfoNodeVisible}
		 sessionProperties={this.context.session_properties}
		 forceRedraw
		 />
		 : null}
            </Panel>
	    );
	    }
	else {
	    return <div className="browser-error"> No viewable data. </div>;
	    }
    }
});


const CollapsingTitle = createReactClass({
    propTypes: {
        title: PropTypes.string.isRequired, // Title to display in the title bar
        handleCollapse: PropTypes.func.isRequired, // Function to call to handle click in collapse button
        collapsed: PropTypes.bool, // T if the panel this is over has been collapsed
    },

    render: function () {
        const { title, handleCollapse, collapsed } = this.props;
        return (
            <div className="collapsing-title">
                <button className="collapsing-title-trigger pull-left" data-trigger onClick={handleCollapse}>{collapseIcon(collapsed, 'collapsing-title-icon')}</button>
                <h4>{title}</h4>
            </div>
        );
    },
});


const FileGraphComponent = createReactClass({
    propTypes: {
        items: PropTypes.array, // Array of annotation information we're graphing
        graph: PropTypes.object, // JsonGraph object generated from files
        setInfoNodeId: PropTypes.func, // Function to call to set the currently selected node ID
        setInfoNodeVisible: PropTypes.func, // Function to call to set the visibility of the node's modal
        infoNodeId: PropTypes.string, // ID of selected node in graph
        infoNodeVisible: PropTypes.bool, // True if node's modal is vibible
        session: PropTypes.object, // Current user's login information
        sessionProperties: PropTypes.object, // True if logged in user is an admin
     },

    getInitialState: function () {
        return {
            infoModalOpen: false, // Graph information modal open
        };
    },

    // Render metadata if a graph node is selected.
    // jsonGraph: JSON graph data.
    // infoNodeId: ID of the selected node
    detailNodes: function (jsonGraph, infoNodeId, session, sessionProperties) {
        let meta;

        // Find data matching selected node, if any
        if (infoNodeId) {
            if (infoNodeId.indexOf('qc:') >= 0) {
                // QC subnode.
                const subnode = jsonGraph.getSubnode(infoNodeId);
                if (subnode) {
                    meta = qcDetailsView(subnode, this.props.schemas);
                    meta.type = subnode['@type'][0];
                }
            } else if (infoNodeId.indexOf('coalesced:') >= 0) {
                // Coalesced contributing files.
                const node = jsonGraph.getNode(infoNodeId);
                if (node) {
                    const currCoalescedFiles = this.state.coalescedFiles;
                    if (currCoalescedFiles[node.metadata.contributing]) {
                        // We have the requested coalesced files in the cache, so just display
                        // them.
                        node.metadata.coalescedFiles = currCoalescedFiles[node.metadata.contributing];
                        meta = coalescedDetailsView(node);
                        meta.type = 'File';
                    } else if (!this.contributingRequestOutstanding) {
                        // We don't have the requested coalesced files in the cache, so we have to
                        // request them from the DB.
                        this.contributingRequestOutstanding = true;
                        requestFiles(node.metadata.ref).then((contributingFiles) => {
                            this.contributingRequestOutstanding = false;
                            currCoalescedFiles[node.metadata.contributing] = contributingFiles;
                            this.setState({ coalescedFiles: currCoalescedFiles });
                        }).catch(() => {
                            this.contributingRequestOutstanding = false;
                            currCoalescedFiles[node.metadata.contributing] = [];
                            this.setState({ coalescedFiles: currCoalescedFiles });
                        });
                    }
                }
            } else {
                // A regular or contributing file.
                const node = jsonGraph.getNode(infoNodeId);
                if (node) {
                    if (node.metadata.contributing) {
                        // This is a contributing file, and its @id is in
                        // node.metadata.contributing. See if the file is in the cache.
                        const currContributing = this.state.contributingFiles;
                        if (currContributing[node.metadata.contributing]) {
                            // We have this file's object in the cache, so just display it.
                            node.metadata.ref = currContributing[node.metadata.contributing];
                            meta = globals.graph_detail.lookup(node)(node, this.handleNodeClick, this.props.auditIndicators, this.props.auditDetail, session, sessionProperties);
                            meta.type = node['@type'][0];
                        } else if (!this.contributingRequestOutstanding) {
                            // We don't have this file's object in the cache, so request it from
                            // the DB.
                            this.contributingRequestOutstanding = true;
                            requestFiles([node.metadata.contributing]).then((contributingFile) => {
                                this.contributingRequestOutstanding = false;
                                currContributing[node.metadata.contributing] = contributingFile[0];
                                this.setState({ contributingFiles: currContributing });
                            }).catch(() => {
                                this.contributingRequestOutstanding = false;
                                currContributing[node.metadata.contributing] = {};
                                this.setState({ contributingFiles: currContributing });
                            });
                        }
                    } else {
                        // Regular File data in the node from when we generated the graph. Just
                        // display the file data from there.
                        meta = globals.graph_detail.lookup(node)(node, this.handleNodeClick, this.props.auditIndicators, this.props.auditDetail, session, sessionProperties);
                        meta.type = node['@type'][0];
                    }
                }
            }
        }

        return meta;
    },


    handleCollapse: function () {
        // Handle click on panel collapse icon
        this.setState({ collapsed: !this.state.collapsed });
    },

    closeModal: function () {
        // Called when user wants to close modal somehow
        this.props.setInfoNodeVisible(false);
    },

    render: function () {
        const { session, sessionProperties, items, graph, infoNodeId, infoNodeVisible } = this.props;
        const files = items;
        const modalTypeMap = {
            File: 'file',
            Step: 'analysis-step',
	    Viz: 'viz',
            QualityMetric: 'quality-metric',
        };
        // If we have a graph, or if we have a selected assembly/annotation, draw the graph panel
	const goodGraph = graph && Object.keys(graph).length;
	const loggedIn = this.context.session && this.context.session['auth.userid'];
	if (goodGraph){
	    const meta = this.detailNodes(graph, infoNodeId, session, sessionProperties);
	    const modalClass = meta ? `graph-modal-${modalTypeMap[meta.type]}` : '';
	    return (
		    <div>
		    <Graph graph={graph} nodeClickHandler={this.handleNodeClick} nodeMouseenterHandler={this.handleHoverIn} nodeMouseleaveHandler={this.handleHoverOut} noDefaultClasses forceRedraw />
		    {meta && infoNodeVisible ?
		     <Modal closeModal={this.closeModal}>
		     <ModalHeader closeModal={this.closeModal} addCss={modalClass}>
		     {meta ? meta.header : null}
		     </ModalHeader>
		     <ModalBody>
		     {meta ? meta.body : null}
		     </ModalBody>
		     <ModalFooter closeModal={<button className="btn btn-info" onClick={this.closeModal}>Close</button>} />
		     </Modal>
			 : null}
		    </div>
	    );
	    return null;
	}
    },
});

const FileGraph = auditDecor(FileGraphComponent);


// Display the metadata of the selected file in the graph
const FileDetailView = function (node, qcClick, auditIndicators, auditDetail, session, sessionProperties) {
    // The node is for a file
    const selectedFile = node.metadata.ref;
    let body = null;
    let header = null;
    const loggedIn = !!(session && session['auth.userid']);
    const adminUser = !!(sessionProperties && sessionProperties.admin);

    if (selectedFile && Object.keys(selectedFile).length) {
        let contributingAccession;

        if (node.metadata.contributing) {
            const accessionStart = selectedFile.dataset.indexOf('/', 1) + 1;
            const accessionEnd = selectedFile.dataset.indexOf('/', accessionStart) - accessionStart;
            contributingAccession = selectedFile.dataset.substr(accessionStart, accessionEnd);
        }
        const dateString = !!selectedFile.date_created && moment.utc(selectedFile.date_created).format('YYYY-MM-DD');
        header = (
            <div className="details-view-info">
                <h4>{selectedFile.file_type} <a href={selectedFile['@id']}>{selectedFile.title}</a></h4>
            </div>
        );

        body = (
            <div>
                <dl className="key-value">
                    {selectedFile.output_type ?
                        <div data-test="output">
                            <dt>Output</dt>
                            <dd>{selectedFile.output_type}</dd>
                        </div>
                    : null}
	    </dl>
            </div>
        );
    } else {
        header = (
            <div className="details-view-info">
                <h4>Unknown</h4>
            </div>
        );
        body = <p className="browser-error">No information available</p>;
    }
    return { header: header, body: body };
};

globals.graph_detail.register(FileDetailView, 'File');
