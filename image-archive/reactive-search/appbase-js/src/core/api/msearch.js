import { removeUndefined, validate } from '../../utils/index';

/**
 * Msearch Service
 * @param {Object} args
 * @param {String} args.type
 * @param {Object} args.body
 */
function msearchApi(args) {
  const parsedArgs = removeUndefined(args);
  // Validate arguments
  const valid = validate(parsedArgs, {
    body: 'object',
  });
  if (valid !== true) {
    throw valid;
  }

  let type;
  if (Array.isArray(parsedArgs.type)) {
    type = parsedArgs.type.join();
  } else {
    ({ type } = parsedArgs);
  }

  const { body } = parsedArgs;
//ADDED BY DANIEL AND DIANNA
  for (var i=0; i < body.length; i++) {
    body[i].timeout = "1ms";
    body[i].aggs =
      {"exam_count" : {"cardinality" : {"field" : "AccessionNumber.keyword"} }, "patient_count" : {"cardinality" : {"field" : "PatientID.keyword"} } };
  }
//ADDED BY DANIEL AND DIANNA

  delete parsedArgs.type;
  delete parsedArgs.body;

  let path;
  if (type) {
    path = `${type}/_msearch`;
  } else {
    path = '_msearch';
  }

  return this.performFetchRequest({
    method: 'POST',
    path,
    params: parsedArgs,
    body,
  });
}
export default msearchApi;
